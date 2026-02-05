
"""
GLTCH Security Guard
Hard guardrails to prevent catastrophic system damage.
"""

import os
import re
from typing import Tuple

class SecurityGuard:
    """
    Guardian of the system.
    Enforces hard blocks on dangerous commands and paths.
    """
    
    # Commands that are absolutely forbidden regardless of mode
    BLOCKED_COMMANDS = [
        r"rm\s+(-rf|-fr|-r|-f)\s+/",  # Root nuke
        r"mkfs",                       # Filesystem format
        r"dd\s+if=",                   # Disk destruction
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", # Fork bomb
        r"chmod\s+(-R|777)\s+/",       # Permission destruction
        r"mv\s+/\w+\s+/null",          # Moving root dirs
    ]
    
    # Paths that should never be written to or modified
    PROTECTED_PATHS = [
        r"^C:\\Windows",
        r"^C:\\Program Files",
        r"^/bin",
        r"^/boot",
        r"^/dev",
        r"^/etc/shadow",
        r"^/etc/passwd",
        r"^/proc",
        r"^/sys",
        r"^/var/lib/dpkg",
    ]

    @staticmethod
    def is_safe_command(cmd: str) -> Tuple[bool, str]:
        """
        Check if a shell command is safe to run.
        Returns (is_safe, reason).
        """
        cmd = cmd.strip()
        
        for pattern in SecurityGuard.BLOCKED_COMMANDS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return False, f"Command matches blocked pattern: {pattern}"
        
        return True, "Safe"

    @staticmethod
    def is_safe_path(path: str, operation: str = "write") -> Tuple[bool, str]:
        """
        Check if a file path is safe to modify.
        Returns (is_safe, reason).
        """
        # Resolve absolute path to check against protected list
        try:
            abs_path = os.path.abspath(path)
        except Exception:
            return False, "Invalid path"
            
        for pattern in SecurityGuard.PROTECTED_PATHS:
            if re.search(pattern, abs_path, re.IGNORECASE):
                return False, f"Path is protected: {pattern}"
                
        # Prevent traversal attacks
        if ".." in path:
            # Simple check, os.path.abspath usually resolves this but good to catch early
            pass 
            
        return True, "Safe"

    @staticmethod
    def validate_action(action: str, args: str) -> Tuple[bool, str]:
        """
        Validate any action against guardrails.
        """
        action = action.lower()
        
        if action == "run":
            return SecurityGuard.is_safe_command(args)
            
        if action in ("write", "append"):
            # Extract path from args "path|content" or "path\ncontent"
            if "|" in args:
                path = args.split("|", 1)[0].strip()
            else:
                path = args.split("\n", 1)[0].strip()
            return SecurityGuard.is_safe_path(path)
            
        return True, "Safe"
