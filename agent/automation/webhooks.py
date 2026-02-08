"""
GLTCH Webhook Manager
Handle incoming webhooks from external services
"""

import asyncio
import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Callable, Awaitable, Any
from enum import Enum


class WebhookStatus(Enum):
    """Webhook endpoint status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class WebhookEvent:
    """Incoming webhook event"""
    id: str
    endpoint_id: str
    source: str
    event_type: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    received_at: datetime = field(default_factory=datetime.now)
    processed: bool = False
    processed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    name: str
    path: str  # URL path: /webhooks/{path}
    
    # Authentication
    secret: Optional[str] = None
    require_signature: bool = False
    signature_header: str = "X-Signature"
    
    # Event handling
    event_type_field: str = "type"
    action: str = "process_webhook"
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Target
    channel: Optional[str] = None
    session_id: Optional[str] = None
    
    # Status
    enabled: bool = True
    status: WebhookStatus = WebhookStatus.ACTIVE
    
    # Stats
    created_at: datetime = field(default_factory=datetime.now)
    last_event: Optional[datetime] = None
    event_count: int = 0
    error_count: int = 0


class WebhookManager:
    """
    Manages webhook endpoints and event processing
    
    Webhooks allow external services to trigger agent actions:
    - GitHub: Repository events
    - Stripe: Payment events
    - Custom: Any HTTP POST
    """
    
    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self._handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self._event_log: List[WebhookEvent] = []
        self._max_log_size = 1000
    
    def register_handler(
        self, 
        action: str, 
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a handler for a webhook action"""
        self._handlers[action] = handler
    
    def add_endpoint(self, endpoint: WebhookEndpoint) -> bool:
        """Add a webhook endpoint"""
        if endpoint.id in self.endpoints:
            return False
        
        # Generate secret if not provided
        if not endpoint.secret and endpoint.require_signature:
            endpoint.secret = self._generate_secret()
        
        self.endpoints[endpoint.id] = endpoint
        return True
    
    def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove a webhook endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False
    
    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """Get endpoint by ID"""
        return self.endpoints.get(endpoint_id)
    
    def get_endpoint_by_path(self, path: str) -> Optional[WebhookEndpoint]:
        """Get endpoint by URL path"""
        for endpoint in self.endpoints.values():
            if endpoint.path == path:
                return endpoint
        return None
    
    def list_endpoints(self) -> List[WebhookEndpoint]:
        """List all endpoints"""
        return list(self.endpoints.values())
    
    async def process_webhook(
        self,
        endpoint_id: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        body: bytes
    ) -> WebhookEvent:
        """
        Process an incoming webhook
        
        Args:
            endpoint_id: The endpoint ID
            payload: Parsed JSON payload
            headers: HTTP headers
            body: Raw request body for signature verification
            
        Returns:
            WebhookEvent with processing result
        """
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_id}")
        
        if not endpoint.enabled or endpoint.status != WebhookStatus.ACTIVE:
            raise ValueError(f"Endpoint is not active: {endpoint_id}")
        
        # Verify signature if required
        if endpoint.require_signature:
            signature = headers.get(endpoint.signature_header, "")
            if not self._verify_signature(body, signature, endpoint.secret):
                raise ValueError("Invalid webhook signature")
        
        # Extract event type
        event_type = payload.get(endpoint.event_type_field, "unknown")
        
        # Create event
        event = WebhookEvent(
            id=self._generate_event_id(),
            endpoint_id=endpoint_id,
            source=endpoint.name,
            event_type=event_type,
            payload=payload,
            headers=dict(headers)
        )
        
        # Process event
        try:
            handler = self._handlers.get(endpoint.action)
            if handler:
                result = await handler(
                    event_type=event_type,
                    payload=payload,
                    channel=endpoint.channel,
                    session_id=endpoint.session_id,
                    **endpoint.params
                )
                event.result = str(result) if result else "OK"
            else:
                event.result = f"No handler for action: {endpoint.action}"
            
            event.processed = True
            event.processed_at = datetime.now()
            endpoint.last_event = datetime.now()
            endpoint.event_count += 1
            
        except Exception as e:
            event.error = str(e)
            endpoint.error_count += 1
        
        # Log event
        self._log_event(event)
        
        return event
    
    def _verify_signature(
        self, 
        body: bytes, 
        signature: str, 
        secret: Optional[str]
    ) -> bool:
        """Verify webhook signature"""
        if not secret:
            return False
        
        # Support common signature formats
        # GitHub: sha256=...
        # Stripe: ...
        
        if signature.startswith("sha256="):
            expected = "sha256=" + hmac.new(
                secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        
        if signature.startswith("sha1="):
            expected = "sha1=" + hmac.new(
                secret.encode(),
                body,
                hashlib.sha1
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        
        # Direct HMAC comparison
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
    
    def _generate_secret(self) -> str:
        """Generate a random webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        import uuid
        return f"evt_{uuid.uuid4().hex[:12]}"
    
    def _log_event(self, event: WebhookEvent) -> None:
        """Log event (with size limit)"""
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
    
    def get_event_log(
        self, 
        endpoint_id: Optional[str] = None,
        limit: int = 50
    ) -> List[WebhookEvent]:
        """Get recent webhook events"""
        events = self._event_log
        if endpoint_id:
            events = [e for e in events if e.endpoint_id == endpoint_id]
        return events[-limit:]
    
    def get_status(self) -> dict:
        """Get webhook manager status"""
        return {
            "total_endpoints": len(self.endpoints),
            "active_endpoints": sum(
                1 for e in self.endpoints.values() 
                if e.status == WebhookStatus.ACTIVE
            ),
            "total_events": len(self._event_log),
            "recent_errors": sum(
                1 for e in self._event_log[-100:] 
                if e.error
            )
        }


# Pre-built webhook templates
def create_github_webhook(
    name: str = "github",
    path: str = "github",
    secret: Optional[str] = None,
    action: str = "notify"
) -> WebhookEndpoint:
    """Create a GitHub webhook endpoint"""
    return WebhookEndpoint(
        id=f"webhook_{name}",
        name=name,
        path=path,
        secret=secret,
        require_signature=bool(secret),
        signature_header="X-Hub-Signature-256",
        event_type_field="action",
        action=action
    )


def create_stripe_webhook(
    name: str = "stripe",
    path: str = "stripe",
    secret: Optional[str] = None,
    action: str = "process_payment"
) -> WebhookEndpoint:
    """Create a Stripe webhook endpoint"""
    return WebhookEndpoint(
        id=f"webhook_{name}",
        name=name,
        path=path,
        secret=secret,
        require_signature=bool(secret),
        signature_header="Stripe-Signature",
        event_type_field="type",
        action=action
    )


def create_generic_webhook(
    id: str,
    name: str,
    path: str,
    action: str = "process_webhook"
) -> WebhookEndpoint:
    """Create a generic webhook endpoint"""
    return WebhookEndpoint(
        id=id,
        name=name,
        path=path,
        require_signature=False,
        action=action
    )
