"""
GLTCH Skills Platform
Extensible skill system for adding new capabilities
"""

import asyncio
import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable
from pathlib import Path
from enum import Enum


class SkillStatus(Enum):
    """Skill status"""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class SkillManifest:
    """Skill manifest (skill.json)"""
    id: str
    name: str
    version: str
    description: str
    author: str
    
    # Entry points
    entry_point: str  # e.g., "main.py" or "skill.js"
    
    # Capabilities
    tools: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    
    # Dependencies
    requires: List[str] = field(default_factory=list)
    python_deps: List[str] = field(default_factory=list)
    node_deps: List[str] = field(default_factory=list)
    
    # Permissions
    permissions: List[str] = field(default_factory=list)
    
    # Config schema
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: str = "MIT"
    tags: List[str] = field(default_factory=list)


@dataclass
class Skill:
    """Installed skill"""
    manifest: SkillManifest
    path: Path
    status: SkillStatus = SkillStatus.INSTALLED
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime
    installed_at: datetime = field(default_factory=datetime.now)
    enabled_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    use_count: int = 0
    error: Optional[str] = None
    
    @property
    def id(self) -> str:
        return self.manifest.id
    
    @property
    def name(self) -> str:
        return self.manifest.name


class SkillsManager:
    """
    Manages skill installation, loading, and execution
    
    Skills are extensible modules that add new capabilities:
    - Tools: New agent tools (e.g., weather, calendar)
    - Commands: New slash commands
    - Triggers: Event-based actions
    """
    
    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = Path(skills_dir or ".gltch/skills")
        self.skills: Dict[str, Skill] = {}
        self._tool_handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self._command_handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
    
    async def initialize(self) -> None:
        """Initialize skills manager and load installed skills"""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        await self.load_installed_skills()
    
    async def load_installed_skills(self) -> None:
        """Load all installed skills from skills directory"""
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                manifest_path = skill_path / "skill.json"
                if manifest_path.exists():
                    try:
                        skill = await self._load_skill(skill_path)
                        if skill:
                            self.skills[skill.id] = skill
                    except Exception as e:
                        print(f"Error loading skill {skill_path.name}: {e}")
    
    async def _load_skill(self, skill_path: Path) -> Optional[Skill]:
        """Load a skill from its directory"""
        manifest_path = skill_path / "skill.json"
        
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        manifest = SkillManifest(**manifest_data)
        
        # Load config if exists
        config = {}
        config_path = skill_path / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        skill = Skill(
            manifest=manifest,
            path=skill_path,
            config=config
        )
        
        return skill
    
    async def install(
        self, 
        source: str,
        enable: bool = True
    ) -> Optional[Skill]:
        """
        Install a skill from source
        
        Args:
            source: URL, path, or skill ID
            enable: Auto-enable after install
            
        Returns:
            Installed Skill or None if failed
        """
        try:
            skill_path = await self._download_skill(source)
            if not skill_path:
                return None
            
            skill = await self._load_skill(skill_path)
            if not skill:
                return None
            
            # Install dependencies
            await self._install_dependencies(skill)
            
            self.skills[skill.id] = skill
            
            if enable:
                await self.enable(skill.id)
            
            return skill
            
        except Exception as e:
            print(f"Error installing skill: {e}")
            return None
    
    async def _download_skill(self, source: str) -> Optional[Path]:
        """Download skill from source"""
        # Local path
        if os.path.isdir(source):
            import shutil
            dest = self.skills_dir / Path(source).name
            shutil.copytree(source, dest)
            return dest
        
        # GitHub URL
        if source.startswith("https://github.com/"):
            return await self._clone_from_github(source)
        
        # Skill registry (future)
        # return await self._download_from_registry(source)
        
        return None
    
    async def _clone_from_github(self, url: str) -> Optional[Path]:
        """Clone skill from GitHub"""
        try:
            import subprocess
            
            # Extract repo name
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            dest = self.skills_dir / repo_name
            
            subprocess.run(
                ['git', 'clone', '--depth', '1', url, str(dest)],
                check=True,
                capture_output=True
            )
            
            return dest
        except Exception:
            return None
    
    async def _install_dependencies(self, skill: Skill) -> None:
        """Install skill dependencies"""
        import subprocess
        
        # Python deps
        if skill.manifest.python_deps:
            subprocess.run(
                ['pip', 'install'] + skill.manifest.python_deps,
                capture_output=True
            )
        
        # Node deps
        if skill.manifest.node_deps:
            subprocess.run(
                ['npm', 'install'] + skill.manifest.node_deps,
                cwd=skill.path,
                capture_output=True
            )
    
    async def uninstall(self, skill_id: str) -> bool:
        """Uninstall a skill"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False
        
        # Disable first
        await self.disable(skill_id)
        
        # Remove directory
        import shutil
        shutil.rmtree(skill.path)
        
        del self.skills[skill_id]
        return True
    
    async def enable(self, skill_id: str) -> bool:
        """Enable a skill"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False
        
        try:
            # Load skill module
            await self._load_skill_module(skill)
            
            skill.status = SkillStatus.ENABLED
            skill.enabled_at = datetime.now()
            skill.error = None
            
            return True
            
        except Exception as e:
            skill.status = SkillStatus.ERROR
            skill.error = str(e)
            return False
    
    async def disable(self, skill_id: str) -> bool:
        """Disable a skill"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False
        
        # Unregister handlers
        for tool in skill.manifest.tools:
            self._tool_handlers.pop(tool, None)
        for cmd in skill.manifest.commands:
            self._command_handlers.pop(cmd, None)
        
        skill.status = SkillStatus.DISABLED
        skill.enabled_at = None
        
        return True
    
    async def _load_skill_module(self, skill: Skill) -> None:
        """Load skill's Python module"""
        entry_point = skill.path / skill.manifest.entry_point
        
        if entry_point.suffix == '.py':
            import importlib.util
            
            spec = importlib.util.spec_from_file_location(
                skill.id, 
                entry_point
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Register tools
                if hasattr(module, 'register_tools'):
                    tools = module.register_tools()
                    for name, handler in tools.items():
                        self._tool_handlers[name] = handler
                
                # Register commands
                if hasattr(module, 'register_commands'):
                    commands = module.register_commands()
                    for name, handler in commands.items():
                        self._command_handlers[name] = handler
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        return self.skills.get(skill_id)
    
    def list_skills(self) -> List[Skill]:
        """List all installed skills"""
        return list(self.skills.values())
    
    def list_enabled_skills(self) -> List[Skill]:
        """List enabled skills"""
        return [s for s in self.skills.values() if s.status == SkillStatus.ENABLED]
    
    def get_tool_handler(self, tool_name: str) -> Optional[Callable]:
        """Get handler for a tool"""
        return self._tool_handlers.get(tool_name)
    
    def get_command_handler(self, command: str) -> Optional[Callable]:
        """Get handler for a command"""
        return self._command_handlers.get(command)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools from enabled skills"""
        return list(self._tool_handlers.keys())
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands from enabled skills"""
        return list(self._command_handlers.keys())
    
    async def execute_tool(
        self, 
        tool_name: str, 
        **kwargs
    ) -> Any:
        """Execute a skill tool"""
        handler = self._tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Track usage
        for skill in self.skills.values():
            if tool_name in skill.manifest.tools:
                skill.last_used = datetime.now()
                skill.use_count += 1
                break
        
        return await handler(**kwargs)
    
    async def execute_command(
        self,
        command: str,
        args: List[str]
    ) -> Any:
        """Execute a skill command"""
        handler = self._command_handlers.get(command)
        if not handler:
            raise ValueError(f"Unknown command: {command}")
        
        return await handler(args)
    
    def configure_skill(
        self, 
        skill_id: str, 
        config: Dict[str, Any]
    ) -> bool:
        """Update skill configuration"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False
        
        skill.config.update(config)
        
        # Save config
        config_path = skill.path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(skill.config, f, indent=2)
        
        return True
    
    def get_status(self) -> dict:
        """Get skills manager status"""
        return {
            "skills_dir": str(self.skills_dir),
            "total_skills": len(self.skills),
            "enabled_skills": len(self.list_enabled_skills()),
            "available_tools": len(self._tool_handlers),
            "available_commands": len(self._command_handlers),
        }
