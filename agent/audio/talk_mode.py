"""
GLTCH Talk Mode Module
Continuous voice conversation mode

Note: Full talk mode requires native app implementation (macOS/iOS/Android).
This module provides the gateway-side infrastructure for talk sessions.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable, Dict, Any
from enum import Enum


class TalkPhase(Enum):
    """Talk mode conversation phase"""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    PAUSED = "paused"


@dataclass  
class TalkConfig:
    """Talk mode configuration"""
    enabled: bool = False
    
    # Voice settings
    voice: str = "en-US-AriaNeural"
    speed: float = 1.0
    
    # Timing settings (seconds)
    silence_threshold: float = 2.0  # Silence before processing
    max_listen_time: float = 30.0   # Max continuous listen time
    response_delay: float = 0.3     # Delay before speaking response
    
    # Behavior
    auto_continue: bool = True      # Auto-continue after response
    interrupt_enabled: bool = True  # Allow interrupting TTS
    
    # Context
    conversation_mode: bool = True  # Maintain conversation context


@dataclass
class TalkSession:
    """Active talk mode session"""
    session_id: str
    started_at: float
    phase: TalkPhase = TalkPhase.IDLE
    turn_count: int = 0
    last_activity: float = field(default_factory=time.time)
    
    # Conversation context
    context: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        self.last_activity = time.time()
    
    def is_stale(self, timeout: float = 300.0) -> bool:
        """Check if session is stale (no activity for timeout seconds)"""
        return time.time() - self.last_activity > timeout


class TalkModeManager:
    """
    Manages talk mode sessions for continuous voice conversation
    
    Talk mode enables hands-free continuous conversation:
    1. Listen for speech
    2. Transcribe to text
    3. Process with agent
    4. Speak response with TTS
    5. Return to listening (if auto_continue)
    """
    
    def __init__(self, config: Optional[TalkConfig] = None):
        self.config = config or TalkConfig()
        self._sessions: Dict[str, TalkSession] = {}
        self._on_message: Optional[Callable[[str, str], Awaitable[str]]] = None
        self._on_speak: Optional[Callable[[str, str], Awaitable[None]]] = None
    
    def set_message_handler(
        self, 
        handler: Callable[[str, str], Awaitable[str]]
    ) -> None:
        """
        Set the message handler for processing talk input
        
        Args:
            handler: Async function(session_id, text) -> response_text
        """
        self._on_message = handler
    
    def set_speak_handler(
        self, 
        handler: Callable[[str, str], Awaitable[None]]
    ) -> None:
        """
        Set the speak handler for TTS output
        
        Args:
            handler: Async function(session_id, text) -> None
        """
        self._on_speak = handler
    
    async def start_session(self, session_id: str) -> TalkSession:
        """Start a new talk mode session"""
        if session_id in self._sessions:
            # Resume existing session
            session = self._sessions[session_id]
            session.phase = TalkPhase.LISTENING
            session.update_activity()
            return session
        
        session = TalkSession(
            session_id=session_id,
            started_at=time.time(),
            phase=TalkPhase.LISTENING
        )
        self._sessions[session_id] = session
        
        print(f"Talk mode started for session: {session_id}")
        return session
    
    async def end_session(self, session_id: str) -> bool:
        """End a talk mode session"""
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            session.phase = TalkPhase.IDLE
            print(f"Talk mode ended for session: {session_id}")
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[TalkSession]:
        """Get an active talk session"""
        return self._sessions.get(session_id)
    
    def is_active(self, session_id: str) -> bool:
        """Check if a talk session is active"""
        session = self._sessions.get(session_id)
        return session is not None and session.phase != TalkPhase.IDLE
    
    async def handle_transcription(
        self, 
        session_id: str, 
        transcription: str
    ) -> Optional[str]:
        """
        Handle transcribed speech from a talk session
        
        Args:
            session_id: The talk session ID
            transcription: Transcribed text
            
        Returns:
            Response text for TTS
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        session.phase = TalkPhase.THINKING
        session.update_activity()
        session.turn_count += 1
        
        try:
            if self._on_message:
                response = await self._on_message(session_id, transcription)
            else:
                response = f"Talk mode received: {transcription}"
            
            # Transition to speaking
            session.phase = TalkPhase.SPEAKING
            
            # Trigger TTS if handler is set
            if self._on_speak and response:
                await self._on_speak(session_id, response)
            
            return response
            
        except Exception as e:
            print(f"Talk mode error: {e}")
            session.phase = TalkPhase.PAUSED
            return None
        
        finally:
            # Return to listening if auto-continue
            if self.config.auto_continue and session.phase == TalkPhase.SPEAKING:
                await asyncio.sleep(self.config.response_delay)
                session.phase = TalkPhase.LISTENING
    
    async def interrupt(self, session_id: str) -> bool:
        """
        Interrupt the current TTS playback
        
        Returns True if interrupted, False if not speaking
        """
        session = self._sessions.get(session_id)
        if not session or session.phase != TalkPhase.SPEAKING:
            return False
        
        if not self.config.interrupt_enabled:
            return False
        
        # Transition back to listening
        session.phase = TalkPhase.LISTENING
        session.update_activity()
        return True
    
    async def pause(self, session_id: str) -> bool:
        """Pause a talk session"""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.phase = TalkPhase.PAUSED
        session.update_activity()
        return True
    
    async def resume(self, session_id: str) -> bool:
        """Resume a paused talk session"""
        session = self._sessions.get(session_id)
        if not session or session.phase != TalkPhase.PAUSED:
            return False
        
        session.phase = TalkPhase.LISTENING
        session.update_activity()
        return True
    
    def get_status(self, session_id: Optional[str] = None) -> dict:
        """Get talk mode status"""
        if session_id:
            session = self._sessions.get(session_id)
            if session:
                return {
                    "enabled": self.config.enabled,
                    "session_id": session_id,
                    "phase": session.phase.value,
                    "turn_count": session.turn_count,
                    "started_at": session.started_at,
                    "last_activity": session.last_activity
                }
            return {"enabled": self.config.enabled, "active": False}
        
        return {
            "enabled": self.config.enabled,
            "active_sessions": len(self._sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "phase": s.phase.value,
                    "turn_count": s.turn_count
                }
                for s in self._sessions.values()
            ]
        }
    
    async def cleanup_stale_sessions(self, timeout: float = 300.0) -> int:
        """Clean up stale talk sessions"""
        stale = [
            sid for sid, session in self._sessions.items()
            if session.is_stale(timeout)
        ]
        
        for sid in stale:
            await self.end_session(sid)
        
        return len(stale)
    
    @classmethod
    def from_env(cls) -> 'TalkModeManager':
        """Create TalkModeManager from environment variables"""
        config = TalkConfig(
            enabled=os.getenv('GLTCH_TALK_MODE_ENABLED', 'false').lower() == 'true',
            voice=os.getenv('GLTCH_TALK_VOICE', 'en-US-AriaNeural'),
            speed=float(os.getenv('GLTCH_TALK_SPEED', '1.0')),
            silence_threshold=float(os.getenv('GLTCH_TALK_SILENCE', '2.0')),
            max_listen_time=float(os.getenv('GLTCH_TALK_MAX_LISTEN', '30.0')),
            auto_continue=os.getenv('GLTCH_TALK_AUTO_CONTINUE', 'true').lower() == 'true',
            interrupt_enabled=os.getenv('GLTCH_TALK_INTERRUPT', 'true').lower() == 'true',
        )
        return cls(config)
