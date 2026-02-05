
import pytest
from agent.tools.security import SecurityGuard

def test_security_blocked_commands():
    """Test standard dangerous commands are blocked."""
    unsafe_commands = [
        "rm -rf /",
        "sudo rm -fr /",
        "mkfs.ext4 /dev/sda",
        ":(){ :|:& };:",
        "chmod 777 /",
        "dd if=/dev/zero of=/dev/sda"
    ]
    for cmd in unsafe_commands:
        safe, reason = SecurityGuard.is_safe_command(cmd)
        assert not safe, f"Should block: {cmd}"
        assert "blocked" in reason.lower()

def test_security_safe_commands():
    """Test safe commands pass."""
    safe_commands = [
        "ls -la",
        "echo hello",
        "cat test.txt",
        "python script.py",
        "nmap 192.168.1.1",
        "rm file.txt" # Deleting single file is "safe" in hard guardrails (users can override via manual confirm)
    ]
    for cmd in safe_commands:
        safe, reason = SecurityGuard.is_safe_command(cmd)
        assert safe, f"Should allow: {cmd}"

def test_security_protected_paths():
    """Test writing to protected paths is blocked."""
    import sys
    
    if sys.platform.startswith("win"):
        unsafe_paths = [
            "C:\\Windows\\System32\\driver.sys",
            "C:\\Program Files\\App\\config.json"
        ]
    else:
        unsafe_paths = [
            "/etc/passwd",
            "/bin/bash",
            "/proc/cpuinfo"
        ]

    for path in unsafe_paths:
        safe, reason = SecurityGuard.is_safe_path(path)
        assert not safe, f"Should block write to: {path}"

def test_security_safe_paths(tmp_path):
    """Test writing to standard paths is allowed."""
    safe, _ = SecurityGuard.is_safe_path(str(tmp_path / "test.txt"))
    assert safe
