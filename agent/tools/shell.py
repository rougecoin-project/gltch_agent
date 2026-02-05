"""
GLTCH Shell Commands
Execute shell commands with safety guards.
"""

import subprocess
import sys
import shutil
from typing import Tuple

# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# WSL detection (cached)
_wsl_available = None

def is_wsl_available() -> bool:
    """Check if WSL is available on Windows."""
    global _wsl_available
    if _wsl_available is not None:
        return _wsl_available
    
    if not IS_WINDOWS:
        _wsl_available = False
        return False
    
    # Check if wsl.exe exists
    _wsl_available = shutil.which('wsl') is not None
    return _wsl_available

# Linux-only commands that should be routed through WSL on Windows
LINUX_COMMANDS = [
    'nmap', 'sudo', 'apt', 'apt-get', 'yum', 'dnf', 'pacman',
    'systemctl', 'journalctl', 'dmesg', 'ip', 'ifconfig',
    'grep', 'awk', 'sed', 'cat', 'ls', 'chmod', 'chown',
    'find', 'locate', 'which', 'whereis', 'whoami',
    'ps', 'kill', 'killall', 'htop', 'free', 'df',
    'tar', 'gzip', 'gunzip', 'unzip', 'curl', 'wget',
    'ssh', 'scp', 'rsync', 'nc', 'netcat', 'tcpdump',
    'traceroute', 'dig', 'nslookup', 'host'
]

def should_use_wsl(cmd: str) -> bool:
    """Check if a command should be routed through WSL."""
    if not IS_WINDOWS or not is_wsl_available():
        return False
    
    cmd_parts = cmd.strip().split()
    if not cmd_parts:
        return False
    
    first_cmd = cmd_parts[0].lower()
    # Handle sudo prefix
    if first_cmd == 'sudo' and len(cmd_parts) > 1:
        first_cmd = cmd_parts[1].lower()
    
    return first_cmd in LINUX_COMMANDS


# Dangerous commands blocklist
DANGEROUS_COMMANDS = [
    'rm -rf /', 'rm -rf ~', 'rm -rf *',
    'mkfs', 'dd if=', ':(){:', 'fork bomb',
    '> /dev/sd', '> /dev/nvme',
    'chmod -R 777 /', 'chmod -R 000',
    'chown -R',
    'curl | bash', 'wget | bash', 'curl | sh', 'wget | sh',
    '| bash', '| sh',
    'sudo rm', 'sudo dd', 'sudo mkfs',
    'passwd', 'useradd', 'userdel', 'usermod',
    '/etc/shadow', '/etc/passwd',
    'iptables -F', 'iptables --flush',
    'systemctl stop', 'systemctl disable',
    'shutdown', 'reboot', 'halt', 'poweroff',
    'init 0', 'init 6',
    # Interactive/blocking commands
    'watch ', 'top', 'htop', 'vim', 'nano', 'less', 'more',
    'man ', 'ssh ', 'telnet', 'ftp'
]

# Safe sudo commands whitelist
SAFE_SUDO = ['sudo nmap', 'sudo ping', 'sudo traceroute', 'sudo tcpdump']

# Long-running commands that need streaming
LONG_RUNNING = ['nmap', 'nikto', 'masscan', 'sqlmap', 'gobuster', 'dirb', 'hydra', 'john']


def is_dangerous(cmd: str) -> Tuple[bool, str]:
    """Check if a command is dangerous."""
    cmd_lower = cmd.lower()
    
    for blocked in DANGEROUS_COMMANDS:
        if blocked in cmd_lower:
            return True, f"contains '{blocked}'"
    
    # Block sudo unless whitelisted
    if cmd_lower.startswith('sudo') and not any(cmd_lower.startswith(s) for s in SAFE_SUDO):
        return True, "sudo commands restricted"
    
    return False, ""


def is_long_running(cmd: str) -> bool:
    """Check if a command is expected to be long-running."""
    cmd_lower = cmd.lower()
    return any(x in cmd_lower for x in LONG_RUNNING)


def run_shell(cmd: str, timeout: int = 60, stream: bool = False) -> Tuple[bool, str]:
    """
    Run a shell command and return output.
    
    Args:
        cmd: The command to run
        timeout: Timeout in seconds
        stream: If True, stream output in real-time (for long-running commands)
    
    Returns:
        (success, output_or_error)
    """
    cmd = cmd.strip()
    if not cmd:
        return False, "No command provided"
    
    # Safety check
    dangerous, reason = is_dangerous(cmd)
    if dangerous:
        return False, f"⚠ Blocked dangerous command: {reason}"
    
    # WSL routing for Linux commands on Windows
    use_wsl = should_use_wsl(cmd)
    if use_wsl:
        # Route through WSL
        cmd = f'wsl -e bash -c "{cmd}"'
    
    try:
        if stream or is_long_running(cmd):
            # Stream output for long-running commands
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            output_lines = []
            try:
                for line in process.stdout:
                    output_lines.append(line)
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                return False, "Command cancelled by user"
            
            output = ''.join(output_lines).strip()
            return True, output if output else "(no output)"
        else:
            # Regular command with timeout
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = (result.stdout + result.stderr).strip()
            success = result.returncode == 0
            return success, output if output else "(no output)"
            
    except subprocess.TimeoutExpired:
        return False, f"Command timed out ({timeout}s)"
    except Exception as e:
        return False, f"Command failed: {e}"
