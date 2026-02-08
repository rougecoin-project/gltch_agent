"""
GLTCH Sandbox Manager
Secure execution environment using Docker
"""

import asyncio
import os
import tempfile
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class SandboxType(Enum):
    """Sandbox types"""
    DOCKER = "docker"
    SUBPROCESS = "subprocess"
    WASM = "wasm"  # Future: WebAssembly sandbox


class ExecutionStatus(Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    enabled: bool = True
    type: SandboxType = SandboxType.DOCKER
    
    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_runtime_seconds: int = 60
    max_output_size_kb: int = 1024
    
    # Network
    network_enabled: bool = False
    allowed_hosts: List[str] = field(default_factory=list)
    
    # File system
    read_only_root: bool = True
    temp_dir_size_mb: int = 100
    
    # Docker settings
    docker_image: str = "python:3.11-slim"
    docker_network: str = "none"


@dataclass
class SandboxedExecution:
    """Sandboxed execution result"""
    id: str
    status: ExecutionStatus
    command: str
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    runtime_seconds: float = 0.0
    
    # Output
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    
    # Errors
    error: Optional[str] = None
    
    # Resource usage
    memory_used_mb: float = 0.0
    cpu_time_seconds: float = 0.0


class SandboxManager:
    """
    Manages sandboxed execution environments
    
    Uses Docker to create isolated execution environments:
    - Limited CPU/memory
    - No network access (by default)
    - Read-only filesystem
    - Timeout enforcement
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._docker_available: Optional[bool] = None
        self._executions: Dict[str, SandboxedExecution] = {}
    
    async def initialize(self) -> bool:
        """Initialize sandbox manager"""
        if self.config.type == SandboxType.DOCKER:
            self._docker_available = await self._check_docker()
            if not self._docker_available:
                print("⚠ Docker not available, falling back to subprocess sandbox")
                self.config.type = SandboxType.SUBPROCESS
        return True
    
    async def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'version',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: Optional[int] = None,
        input_data: Optional[str] = None
    ) -> SandboxedExecution:
        """
        Execute code in a sandbox
        
        Args:
            code: Code to execute
            language: Programming language
            timeout: Max execution time (seconds)
            input_data: stdin input
            
        Returns:
            SandboxedExecution result
        """
        import uuid
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        timeout = timeout or self.config.max_runtime_seconds
        
        if self.config.type == SandboxType.DOCKER:
            result = await self._execute_docker(exec_id, code, language, timeout, input_data)
        else:
            result = await self._execute_subprocess(exec_id, code, language, timeout, input_data)
        
        self._executions[exec_id] = result
        return result
    
    async def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_dir: Optional[str] = None
    ) -> SandboxedExecution:
        """
        Execute a shell command in a sandbox
        
        Args:
            command: Shell command
            timeout: Max execution time
            working_dir: Working directory
            
        Returns:
            SandboxedExecution result
        """
        import uuid
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        timeout = timeout or self.config.max_runtime_seconds
        
        if self.config.type == SandboxType.DOCKER:
            result = await self._execute_docker_command(exec_id, command, timeout, working_dir)
        else:
            result = await self._execute_subprocess_command(exec_id, command, timeout, working_dir)
        
        self._executions[exec_id] = result
        return result
    
    async def _execute_docker(
        self,
        exec_id: str,
        code: str,
        language: str,
        timeout: int,
        input_data: Optional[str]
    ) -> SandboxedExecution:
        """Execute code in Docker container"""
        execution = SandboxedExecution(
            id=exec_id,
            status=ExecutionStatus.PENDING,
            command=f"run {language} code"
        )
        
        # Create temp file for code
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=self._get_extension(language),
            delete=False
        ) as f:
            f.write(code)
            code_file = f.name
        
        try:
            # Build Docker command
            docker_cmd = [
                'docker', 'run',
                '--rm',
                '--network', self.config.docker_network if not self.config.network_enabled else 'bridge',
                '--memory', f'{self.config.max_memory_mb}m',
                '--cpus', str(self.config.max_cpu_percent / 100),
                '--read-only' if self.config.read_only_root else '',
                '-v', f'{code_file}:/code/main{self._get_extension(language)}:ro',
                self.config.docker_image,
                self._get_run_command(language)
            ]
            docker_cmd = [c for c in docker_cmd if c]  # Remove empty strings
            
            execution.started_at = datetime.now()
            execution.status = ExecutionStatus.RUNNING
            
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input_data.encode() if input_data else None),
                    timeout=timeout
                )
                
                execution.stdout = self._truncate_output(stdout.decode())
                execution.stderr = self._truncate_output(stderr.decode())
                execution.exit_code = proc.returncode
                execution.status = ExecutionStatus.COMPLETED if proc.returncode == 0 else ExecutionStatus.FAILED
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                execution.status = ExecutionStatus.TIMEOUT
                execution.error = f"Execution timed out after {timeout}s"
            
            execution.completed_at = datetime.now()
            execution.runtime_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
        finally:
            os.unlink(code_file)
        
        return execution
    
    async def _execute_subprocess(
        self,
        exec_id: str,
        code: str,
        language: str,
        timeout: int,
        input_data: Optional[str]
    ) -> SandboxedExecution:
        """Execute code in subprocess (less secure fallback)"""
        execution = SandboxedExecution(
            id=exec_id,
            status=ExecutionStatus.PENDING,
            command=f"run {language} code"
        )
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_extension(language),
            delete=False
        ) as f:
            f.write(code)
            code_file = f.name
        
        try:
            cmd = self._get_interpreter(language) + [code_file]
            
            execution.started_at = datetime.now()
            execution.status = ExecutionStatus.RUNNING
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input_data.encode() if input_data else None),
                    timeout=timeout
                )
                
                execution.stdout = self._truncate_output(stdout.decode())
                execution.stderr = self._truncate_output(stderr.decode())
                execution.exit_code = proc.returncode
                execution.status = ExecutionStatus.COMPLETED if proc.returncode == 0 else ExecutionStatus.FAILED
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                execution.status = ExecutionStatus.TIMEOUT
                execution.error = f"Execution timed out after {timeout}s"
            
            execution.completed_at = datetime.now()
            execution.runtime_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
        finally:
            os.unlink(code_file)
        
        return execution
    
    async def _execute_docker_command(
        self,
        exec_id: str,
        command: str,
        timeout: int,
        working_dir: Optional[str]
    ) -> SandboxedExecution:
        """Execute shell command in Docker"""
        execution = SandboxedExecution(
            id=exec_id,
            status=ExecutionStatus.PENDING,
            command=command
        )
        
        try:
            docker_cmd = [
                'docker', 'run',
                '--rm',
                '--network', self.config.docker_network,
                '--memory', f'{self.config.max_memory_mb}m',
                self.config.docker_image,
                'sh', '-c', command
            ]
            
            execution.started_at = datetime.now()
            execution.status = ExecutionStatus.RUNNING
            
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                execution.stdout = self._truncate_output(stdout.decode())
                execution.stderr = self._truncate_output(stderr.decode())
                execution.exit_code = proc.returncode
                execution.status = ExecutionStatus.COMPLETED if proc.returncode == 0 else ExecutionStatus.FAILED
                
            except asyncio.TimeoutError:
                proc.kill()
                execution.status = ExecutionStatus.TIMEOUT
            
            execution.completed_at = datetime.now()
            execution.runtime_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
        
        return execution
    
    async def _execute_subprocess_command(
        self,
        exec_id: str,
        command: str,
        timeout: int,
        working_dir: Optional[str]
    ) -> SandboxedExecution:
        """Execute shell command in subprocess"""
        execution = SandboxedExecution(
            id=exec_id,
            status=ExecutionStatus.PENDING,
            command=command
        )
        
        try:
            execution.started_at = datetime.now()
            execution.status = ExecutionStatus.RUNNING
            
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                execution.stdout = self._truncate_output(stdout.decode())
                execution.stderr = self._truncate_output(stderr.decode())
                execution.exit_code = proc.returncode
                execution.status = ExecutionStatus.COMPLETED if proc.returncode == 0 else ExecutionStatus.FAILED
                
            except asyncio.TimeoutError:
                proc.kill()
                execution.status = ExecutionStatus.TIMEOUT
            
            execution.completed_at = datetime.now()
            execution.runtime_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
        
        return execution
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'ruby': '.rb',
            'go': '.go',
            'rust': '.rs',
            'bash': '.sh',
            'shell': '.sh',
        }
        return extensions.get(language.lower(), '.txt')
    
    def _get_interpreter(self, language: str) -> List[str]:
        """Get interpreter command for language"""
        interpreters = {
            'python': ['python3'],
            'javascript': ['node'],
            'typescript': ['npx', 'ts-node'],
            'ruby': ['ruby'],
            'bash': ['bash'],
            'shell': ['sh'],
        }
        return interpreters.get(language.lower(), ['cat'])
    
    def _get_run_command(self, language: str) -> str:
        """Get run command for Docker"""
        commands = {
            'python': 'python3 /code/main.py',
            'javascript': 'node /code/main.js',
            'bash': 'bash /code/main.sh',
        }
        return commands.get(language.lower(), 'cat /code/main.txt')
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output to max size"""
        max_bytes = self.config.max_output_size_kb * 1024
        if len(output) > max_bytes:
            return output[:max_bytes] + "\n... (output truncated)"
        return output
    
    def get_execution(self, exec_id: str) -> Optional[SandboxedExecution]:
        """Get execution by ID"""
        return self._executions.get(exec_id)
    
    def get_status(self) -> dict:
        """Get sandbox manager status"""
        return {
            "enabled": self.config.enabled,
            "type": self.config.type.value,
            "docker_available": self._docker_available,
            "total_executions": len(self._executions),
        }
    
    @classmethod
    def from_env(cls) -> 'SandboxManager':
        """Create from environment variables"""
        config = SandboxConfig(
            enabled=os.getenv('GLTCH_SANDBOX_ENABLED', 'true').lower() == 'true',
            max_memory_mb=int(os.getenv('GLTCH_SANDBOX_MEMORY', '512')),
            max_runtime_seconds=int(os.getenv('GLTCH_SANDBOX_TIMEOUT', '60')),
            network_enabled=os.getenv('GLTCH_SANDBOX_NETWORK', 'false').lower() == 'true',
        )
        return cls(config)
