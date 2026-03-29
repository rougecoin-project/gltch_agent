"""
GLTCH Integration Base
Abstract base class for external service integrations.
"""

import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class IntegrationStatus(Enum):
    """Integration connection status"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class Integration(ABC):
    """
    Base class for external service integrations.

    All integrations:
    - Use REST APIs (no SDK dependencies)
    - Respect the /net toggle
    - Store config in memory.json under "integrations" key
    - Are poll-based (called by BackgroundDaemon)
    """

    def __init__(self, name: str):
        self.name = name
        self.status = IntegrationStatus.DISCONNECTED
        self.token: Optional[str] = None
        self.last_poll: Optional[str] = None
        self.last_error: Optional[str] = None
        self._poll_count = 0

    @abstractmethod
    def connect(self, token: str, **kwargs) -> bool:
        """Connect to the service with the given token."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the service."""
        pass

    @abstractmethod
    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new events. Returns list of event dicts."""
        pass

    @abstractmethod
    def send(self, target: str, message: str, **kwargs) -> bool:
        """Send a message/action to the service."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            "name": self.name,
            "status": self.status.value,
            "connected": self.status == IntegrationStatus.CONNECTED,
            "last_poll": self.last_poll,
            "last_error": self.last_error,
            "poll_count": self._poll_count
        }

    def get_config(self) -> Dict[str, Any]:
        """Get config for persistence in memory.json."""
        return {
            "name": self.name,
            "token": self.token,
            "status": self.status.value
        }

    def _http_get(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Dict[str, Any]:
        """Make an HTTP GET request."""
        req = urllib.request.Request(url, method="GET")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.status = IntegrationStatus.RATE_LIMITED
            raise

    def _http_post(self, url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Dict[str, Any]:
        """Make an HTTP POST request."""
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.status = IntegrationStatus.RATE_LIMITED
            raise
