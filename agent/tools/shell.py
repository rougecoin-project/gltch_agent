"""
GLTCH Shell Commands
Execute shell commands with safety guards.
"""

import subprocess
from typing import Tuple


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
