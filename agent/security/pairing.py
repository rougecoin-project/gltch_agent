"""
GLTCH DM Pairing
Secure pairing system for DM approval
"""

import asyncio
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Awaitable
from enum import Enum


class PairingStatus(Enum):
    """Pairing session status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class PairingConfig:
    """Pairing configuration"""
    enabled: bool = True
    code_length: int = 6
    code_expires_minutes: int = 15
    max_attempts: int = 3
    cooldown_minutes: int = 60
    require_secondary_verification: bool = False
    allowed_channels: List[str] = field(default_factory=lambda: ["telegram", "whatsapp", "signal"])


@dataclass
class PairingSession:
    """Active pairing session"""
    id: str
    channel: str
    sender_id: str
    sender_name: Optional[str] = None
    
    # Pairing code
    code: str = ""
    code_expires_at: Optional[datetime] = None
    
    # Status
    status: PairingStatus = PairingStatus.PENDING
    attempts: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        if self.code_expires_at:
            return datetime.now() > self.code_expires_at
        return False


@dataclass
class ApprovedSender:
    """Approved DM sender"""
    sender_id: str
    channel: str
    sender_name: Optional[str] = None
    approved_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class PairingManager:
    """
    Manages DM pairing and approval
    
    Pairing flow:
    1. New DM arrives from unknown sender
    2. Generate pairing code
    3. Send code via alternative channel (or display in dashboard)
    4. Sender enters code to verify
    5. Owner approves/rejects
    6. If approved, sender added to allowlist
    """
    
    def __init__(self, config: Optional[PairingConfig] = None):
        self.config = config or PairingConfig()
        self.sessions: Dict[str, PairingSession] = {}
        self.approved: Dict[str, ApprovedSender] = {}
        self.blocked: Dict[str, datetime] = {}  # sender_id -> blocked_until
        self._cooldowns: Dict[str, datetime] = {}  # sender_id -> cooldown_until
        
        # Callbacks
        self._on_pairing_request: Optional[Callable[[PairingSession], Awaitable[None]]] = None
        self._on_pairing_verified: Optional[Callable[[PairingSession], Awaitable[None]]] = None
    
    def on_pairing_request(
        self, 
        callback: Callable[[PairingSession], Awaitable[None]]
    ) -> None:
        """Set callback for new pairing requests"""
        self._on_pairing_request = callback
    
    def on_pairing_verified(
        self, 
        callback: Callable[[PairingSession], Awaitable[None]]
    ) -> None:
        """Set callback for verified pairings"""
        self._on_pairing_verified = callback
    
    async def handle_new_dm(
        self,
        channel: str,
        sender_id: str,
        sender_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[PairingSession]:
        """
        Handle a new DM from an unknown sender
        
        Returns PairingSession if pairing is required, None if already approved
        """
        if not self.config.enabled:
            return None
        
        # Check if channel requires pairing
        if channel not in self.config.allowed_channels:
            return None
        
        # Check if already approved
        key = f"{channel}:{sender_id}"
        if key in self.approved:
            return None
        
        # Check if blocked
        if key in self.blocked:
            if datetime.now() < self.blocked[key]:
                return None  # Still blocked
            else:
                del self.blocked[key]
        
        # Check cooldown
        if key in self._cooldowns:
            if datetime.now() < self._cooldowns[key]:
                return None  # In cooldown
        
        # Check for existing session
        existing = self.sessions.get(key)
        if existing and not existing.is_expired:
            return existing
        
        # Create new pairing session
        session = await self.create_pairing_session(
            channel=channel,
            sender_id=sender_id,
            sender_name=sender_name,
            metadata=metadata or {}
        )
        
        return session
    
    async def create_pairing_session(
        self,
        channel: str,
        sender_id: str,
        sender_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> PairingSession:
        """Create a new pairing session"""
        session_id = f"pair_{secrets.token_hex(8)}"
        code = self._generate_code()
        
        session = PairingSession(
            id=session_id,
            channel=channel,
            sender_id=sender_id,
            sender_name=sender_name,
            code=code,
            code_expires_at=datetime.now() + timedelta(minutes=self.config.code_expires_minutes),
            metadata=metadata or {}
        )
        
        key = f"{channel}:{sender_id}"
        self.sessions[key] = session
        
        # Notify callback
        if self._on_pairing_request:
            await self._on_pairing_request(session)
        
        return session
    
    async def verify_code(
        self,
        channel: str,
        sender_id: str,
        code: str
    ) -> tuple[bool, str]:
        """
        Verify a pairing code
        
        Returns (success, message)
        """
        key = f"{channel}:{sender_id}"
        session = self.sessions.get(key)
        
        if not session:
            return False, "No active pairing session"
        
        if session.is_expired:
            return False, "Pairing code has expired"
        
        session.attempts += 1
        
        if session.attempts > self.config.max_attempts:
            # Block sender
            del self.sessions[key]
            self._cooldowns[key] = datetime.now() + timedelta(
                minutes=self.config.cooldown_minutes
            )
            return False, "Too many attempts. Please try again later."
        
        if session.code.upper() != code.upper():
            return False, f"Invalid code. {self.config.max_attempts - session.attempts} attempts remaining."
        
        # Code verified
        session.status = PairingStatus.PENDING
        session.verified_at = datetime.now()
        
        # Notify callback
        if self._on_pairing_verified:
            await self._on_pairing_verified(session)
        
        return True, "Code verified! Waiting for approval."
    
    async def approve(
        self,
        channel: str,
        sender_id: str,
        approved_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Approve a pairing request"""
        key = f"{channel}:{sender_id}"
        session = self.sessions.get(key)
        
        if not session:
            return False
        
        session.status = PairingStatus.APPROVED
        session.approved_at = datetime.now()
        session.approved_by = approved_by
        
        # Add to approved list
        self.approved[key] = ApprovedSender(
            sender_id=sender_id,
            channel=channel,
            sender_name=session.sender_name,
            approved_by=approved_by,
            notes=notes
        )
        
        # Clean up session
        del self.sessions[key]
        
        return True
    
    async def reject(
        self,
        channel: str,
        sender_id: str,
        block: bool = False,
        block_duration_hours: int = 24
    ) -> bool:
        """Reject a pairing request"""
        key = f"{channel}:{sender_id}"
        session = self.sessions.get(key)
        
        if not session:
            return False
        
        session.status = PairingStatus.REJECTED
        
        if block:
            self.blocked[key] = datetime.now() + timedelta(hours=block_duration_hours)
        
        # Clean up session
        del self.sessions[key]
        
        return True
    
    def is_approved(self, channel: str, sender_id: str) -> bool:
        """Check if a sender is approved"""
        key = f"{channel}:{sender_id}"
        return key in self.approved
    
    def revoke(self, channel: str, sender_id: str) -> bool:
        """Revoke approval for a sender"""
        key = f"{channel}:{sender_id}"
        if key in self.approved:
            del self.approved[key]
            return True
        return False
    
    def list_approved(self) -> List[ApprovedSender]:
        """List all approved senders"""
        return list(self.approved.values())
    
    def list_pending(self) -> List[PairingSession]:
        """List pending pairing sessions"""
        return [s for s in self.sessions.values() if s.status == PairingStatus.PENDING]
    
    def _generate_code(self) -> str:
        """Generate a pairing code"""
        # Alphanumeric, no confusing characters (0, O, 1, I, L)
        alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
        return ''.join(secrets.choice(alphabet) for _ in range(self.config.code_length))
    
    def get_status(self) -> dict:
        """Get pairing manager status"""
        return {
            "enabled": self.config.enabled,
            "approved_count": len(self.approved),
            "pending_count": len(self.sessions),
            "blocked_count": len(self.blocked),
        }
    
    @classmethod
    def from_env(cls) -> 'PairingManager':
        """Create from environment variables"""
        config = PairingConfig(
            enabled=os.getenv('GLTCH_PAIRING_ENABLED', 'false').lower() == 'true',
            code_length=int(os.getenv('GLTCH_PAIRING_CODE_LENGTH', '6')),
            code_expires_minutes=int(os.getenv('GLTCH_PAIRING_EXPIRES', '15')),
            max_attempts=int(os.getenv('GLTCH_PAIRING_MAX_ATTEMPTS', '3')),
        )
        return cls(config)
