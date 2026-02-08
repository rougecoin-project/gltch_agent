"""
GLTCH Voice Wake Module
Wake word detection for triggering voice interactions

Note: Full voice wake requires native app implementation (macOS/iOS/Android).
This module provides the gateway-side infrastructure for handling wake events.
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Awaitable
from enum import Enum


class VoiceWakeState(Enum):
    """Voice wake detection state"""
    DISABLED = "disabled"
    IDLE = "idle"
    LISTENING = "listening"
    TRIGGERED = "triggered"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class VoiceWakeConfig:
    """Voice wake configuration"""
    enabled: bool = False
    
    # Wake words (case-insensitive)
    wake_words: List[str] = field(default_factory=lambda: ["gltch", "hey gltch", "computer"])
    
    # Sensitivity (0.0 to 1.0)
    sensitivity: float = 0.5
    
    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    
    # Timeout settings (seconds)
    listen_timeout: float = 10.0  # Max time to listen after wake word
    silence_threshold: float = 2.0  # Silence before stopping


@dataclass
class VoiceWakeEvent:
    """Event triggered when wake word is detected"""
    wake_word: str
    confidence: float
    timestamp: float
    audio_data: Optional[bytes] = None
    transcription: Optional[str] = None


class VoiceWakeManager:
    """
    Manages voice wake detection and events
    
    The actual wake word detection happens in native apps.
    This manager handles the gateway-side coordination.
    """
    
    def __init__(self, config: Optional[VoiceWakeConfig] = None):
        self.config = config or VoiceWakeConfig()
        self.state = VoiceWakeState.DISABLED if not self.config.enabled else VoiceWakeState.IDLE
        self._listeners: List[Callable[[VoiceWakeEvent], Awaitable[None]]] = []
        self._active_session: Optional[str] = None
    
    def enable(self) -> None:
        """Enable voice wake detection"""
        self.config.enabled = True
        self.state = VoiceWakeState.IDLE
    
    def disable(self) -> None:
        """Disable voice wake detection"""
        self.config.enabled = False
        self.state = VoiceWakeState.DISABLED
    
    def get_wake_words(self) -> List[str]:
        """Get configured wake words"""
        return self.config.wake_words.copy()
    
    def set_wake_words(self, words: List[str]) -> None:
        """Set wake words"""
        self.config.wake_words = [w.lower() for w in words]
    
    def add_wake_word(self, word: str) -> None:
        """Add a wake word"""
        word = word.lower()
        if word not in self.config.wake_words:
            self.config.wake_words.append(word)
    
    def remove_wake_word(self, word: str) -> None:
        """Remove a wake word"""
        word = word.lower()
        if word in self.config.wake_words:
            self.config.wake_words.remove(word)
    
    def on_wake(self, callback: Callable[[VoiceWakeEvent], Awaitable[None]]) -> None:
        """Register a callback for wake events"""
        self._listeners.append(callback)
    
    async def handle_wake_event(self, event: VoiceWakeEvent) -> None:
        """
        Handle a wake event from a native app
        
        Called when a native app detects a wake word and
        forwards the event to the gateway.
        """
        if not self.config.enabled:
            return
        
        self.state = VoiceWakeState.TRIGGERED
        
        # Notify all listeners
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception as e:
                print(f"Voice wake listener error: {e}")
        
        self.state = VoiceWakeState.IDLE
    
    async def process_transcription(
        self, 
        transcription: str,
        session_id: str
    ) -> Optional[str]:
        """
        Process a transcribed voice command
        
        Args:
            transcription: The transcribed text from voice input
            session_id: Session ID for routing
            
        Returns:
            Response text (for TTS) if any
        """
        self.state = VoiceWakeState.PROCESSING
        self._active_session = session_id
        
        try:
            # Remove wake word prefix if present
            cleaned = self._strip_wake_word(transcription)
            
            if not cleaned:
                return None
            
            # The actual agent routing is handled by the caller
            # This just returns the cleaned transcription
            return cleaned
            
        finally:
            self.state = VoiceWakeState.IDLE
            self._active_session = None
    
    def _strip_wake_word(self, text: str) -> str:
        """Remove wake word from beginning of text"""
        text_lower = text.lower().strip()
        
        for wake_word in self.config.wake_words:
            if text_lower.startswith(wake_word):
                return text[len(wake_word):].strip()
        
        return text.strip()
    
    def is_wake_word(self, text: str) -> bool:
        """Check if text starts with a wake word"""
        text_lower = text.lower().strip()
        return any(text_lower.startswith(w) for w in self.config.wake_words)
    
    def get_state(self) -> VoiceWakeState:
        """Get current voice wake state"""
        return self.state
    
    def get_status(self) -> dict:
        """Get voice wake status"""
        return {
            "enabled": self.config.enabled,
            "state": self.state.value,
            "wake_words": self.config.wake_words,
            "sensitivity": self.config.sensitivity,
            "active_session": self._active_session
        }
    
    @classmethod
    def from_env(cls) -> 'VoiceWakeManager':
        """Create VoiceWakeManager from environment variables"""
        wake_words_str = os.getenv('GLTCH_WAKE_WORDS', 'gltch,hey gltch,computer')
        wake_words = [w.strip() for w in wake_words_str.split(',') if w.strip()]
        
        config = VoiceWakeConfig(
            enabled=os.getenv('GLTCH_VOICE_WAKE_ENABLED', 'false').lower() == 'true',
            wake_words=wake_words,
            sensitivity=float(os.getenv('GLTCH_WAKE_SENSITIVITY', '0.5')),
            listen_timeout=float(os.getenv('GLTCH_WAKE_LISTEN_TIMEOUT', '10.0')),
            silence_threshold=float(os.getenv('GLTCH_WAKE_SILENCE_THRESHOLD', '2.0')),
        )
        return cls(config)
