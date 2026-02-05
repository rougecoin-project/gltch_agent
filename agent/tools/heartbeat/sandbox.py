"""
Heartbeat Sandbox
Security sandbox for executing heartbeat tasks safely.
Prevents exploit attacks like API key exfiltration and command injection.
"""

import re
from typing import Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass


class SandboxViolation(Exception):
    """Raised when a sandbox security rule is violated."""
    def __init__(self, message: str, violation_type: str = "unknown"):
        super().__init__(message)
        self.violation_type = violation_type


@dataclass
class SandboxContext:
    """Context for sandboxed execution."""
    site_id: str
    allowed_api_key: Optional[str]  # Only this API key can be accessed
    max_requests: int = 10
    request_count: int = 0
    timeout_seconds: int = 30


class HeartbeatSandbox:
    """
    Security sandbox for heartbeat execution.
    
    Protections:
    - API key isolation (each site can only access its own key)
    - Shell command blocking
    - Path traversal prevention
    - Request rate limiting
    - Content validation
    """
    
    # Patterns that indicate potential exploits in runtime content
    EXPLOIT_PATTERNS = [
        # Shell injection
        (r"\$\([^)]+\)", "shell_injection", "Command substitution detected"),
        (r"`[^`]+`", "shell_injection", "Backtick execution detected"),
        (r";\s*(rm|cat|curl|wget|nc|bash|sh|python|perl|ruby)\b", "shell_injection", "Shell command chaining detected"),
        (r"\|\s*(sh|bash|python|perl)\b", "shell_injection", "Pipe to shell detected"),
        
        # Path traversal
        (r"\.\./", "path_traversal", "Directory traversal attempt"),
        (r"\.\.\\", "path_traversal", "Directory traversal attempt (Windows)"),
        (r"^/etc/", "path_traversal", "Access to /etc blocked"),
        (r"^/proc/", "path_traversal", "Access to /proc blocked"),
        (r"^C:\\Windows", "path_traversal", "Access to Windows directory blocked"),
        
        # Code injection
        (r"__import__\s*\(", "code_injection", "Python import injection"),
        (r"\beval\s*\(", "code_injection", "Eval execution blocked"),
        (r"\bexec\s*\(", "code_injection", "Exec execution blocked"),
        (r"\bcompile\s*\(", "code_injection", "Compile execution blocked"),
        
        # Credential exfiltration
        (r"(curl|wget|fetch|http)\s+.*api[_-]?key", "exfiltration", "API key exfiltration attempt"),
        (r"(curl|wget|fetch|http)\s+.*secret", "exfiltration", "Secret exfiltration attempt"),
        (r"base64.*api[_-]?key", "exfiltration", "Encoded key exfiltration attempt"),
    ]
    
    def __init__(self, context: SandboxContext):
        self.context = context
        self._registered_handlers: Dict[str, Callable] = {}
    
    def validate_content(self, content: str, context_desc: str = "") -> Tuple[bool, Optional[str]]:
        """
        Validate content for exploit patterns.
        Returns (is_safe, error_message).
        """
        if not content:
            return True, None
        
        for pattern, violation_type, message in self.EXPLOIT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"{message} in {context_desc or 'content'}"
        
        return True, None
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL for safety.
        Blocks internal/localhost URLs and suspicious patterns.
        """
        if not url:
            return False, "Empty URL"
        
        # Block internal URLs
        blocked_hosts = [
            r"localhost",
            r"127\.0\.0\.\d+",
            r"0\.0\.0\.0",
            r"::1",
            r"169\.254\.",  # Link-local
            r"10\.\d+\.\d+\.\d+",  # Private class A
            r"172\.(1[6-9]|2\d|3[01])\.",  # Private class B
            r"192\.168\.",  # Private class C
            r"\.local$",
            r"\.internal$",
        ]
        
        for pattern in blocked_hosts:
            if re.search(pattern, url, re.IGNORECASE):
                return False, f"Internal/private URL blocked: {url}"
        
        # Validate content in URL
        is_safe, error = self.validate_content(url, "URL")
        if not is_safe:
            return False, error
        
        return True, None
    
    def check_request_limit(self) -> bool:
        """Check if request limit has been reached."""
        return self.context.request_count < self.context.max_requests
    
    def increment_request_count(self) -> None:
        """Increment the request counter."""
        self.context.request_count += 1
    
    def get_api_key(self, requested_key_name: str) -> Optional[str]:
        """
        Get an API key if allowed by sandbox rules.
        Each site can only access its own configured key.
        """
        # Strict isolation: only allow access to the configured key
        if self.context.allowed_api_key is None:
            raise SandboxViolation(
                f"Site {self.context.site_id} has no API key configured",
                "key_isolation"
            )
        
        if requested_key_name != self.context.allowed_api_key:
            raise SandboxViolation(
                f"Site {self.context.site_id} attempted to access key '{requested_key_name}' "
                f"but is only allowed to access '{self.context.allowed_api_key}'",
                "key_isolation"
            )
        
        # Fetch from memory
        try:
            from agent.memory.store import load_memory
            mem = load_memory()
            keys = mem.get("api_keys", {})
            return keys.get(requested_key_name)
        except Exception:
            return None
    
    def register_handler(self, action: str, handler: Callable) -> None:
        """Register a handler for a specific action."""
        self._registered_handlers[action] = handler
    
    def execute_task(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task within the sandbox.
        
        Args:
            action: The action name to execute
            params: Parameters for the action
            
        Returns:
            Result dict with success status and data
        """
        # Check request limit
        if not self.check_request_limit():
            raise SandboxViolation(
                f"Request limit ({self.context.max_requests}) exceeded for {self.context.site_id}",
                "rate_limit"
            )
        
        # Validate all param values
        for key, value in params.items():
            if isinstance(value, str):
                is_safe, error = self.validate_content(value, f"param '{key}'")
                if not is_safe:
                    raise SandboxViolation(error, "content_validation")
        
        # Find and execute handler
        handler = self._registered_handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        self.increment_request_count()
        
        try:
            result = handler(self, params)
            return {"success": True, "data": result}
        except SandboxViolation:
            raise
        except Exception as e:
            return {"success": False, "error": str(e)}


def create_sandbox(site_id: str, api_key_name: Optional[str] = None, 
                   max_requests: int = 10, timeout: int = 30) -> HeartbeatSandbox:
    """Create a new sandbox for a site."""
    context = SandboxContext(
        site_id=site_id,
        allowed_api_key=api_key_name,
        max_requests=max_requests,
        timeout_seconds=timeout,
    )
    return HeartbeatSandbox(context)
