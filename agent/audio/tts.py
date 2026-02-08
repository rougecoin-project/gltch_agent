"""
GLTCH Text-to-Speech Module
Supports multiple TTS providers: Edge TTS (free), ElevenLabs, OpenAI
"""

import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
import re


class TTSProvider(Enum):
    """Available TTS providers"""
    EDGE = "edge"          # Microsoft Edge TTS (free)
    ELEVENLABS = "elevenlabs"  # ElevenLabs (premium)
    OPENAI = "openai"      # OpenAI TTS


class TTSMode(Enum):
    """TTS auto-trigger modes"""
    OFF = "off"           # Never auto-speak
    ALWAYS = "always"     # Always speak responses
    INBOUND = "inbound"   # Speak when triggered by voice input
    TAGGED = "tagged"     # Only speak when response contains [[tts:...]] tag


@dataclass
class TTSConfig:
    """TTS configuration"""
    enabled: bool = False
    provider: TTSProvider = TTSProvider.EDGE
    mode: TTSMode = TTSMode.OFF
    
    # Voice settings
    voice: str = "en-US-AriaNeural"  # Default Edge voice
    speed: float = 1.0
    pitch: float = 1.0
    
    # Provider-specific settings
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    elevenlabs_model: str = "eleven_monolingual_v1"
    
    openai_api_key: Optional[str] = None
    openai_voice: str = "nova"  # alloy, echo, fable, onyx, nova, shimmer
    openai_model: str = "tts-1"  # tts-1 or tts-1-hd
    
    # Output settings
    max_text_length: int = 4096  # Summarize longer texts
    output_format: str = "mp3"


@dataclass
class TTSDirective:
    """Parsed TTS directive from response text"""
    voice: Optional[str] = None
    speed: Optional[float] = None
    emotion: Optional[str] = None
    skip: bool = False


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers"""
    
    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        voice: str, 
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """Synthesize speech from text, returns audio bytes"""
        pass
    
    @abstractmethod
    def get_voices(self) -> list[Dict[str, Any]]:
        """Get list of available voices"""
        pass


class EdgeTTSProvider(BaseTTSProvider):
    """Microsoft Edge TTS provider (free)"""
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts not installed. Run: pip install edge-tts")
        
        # Apply speed adjustment
        rate = f"+{int((speed - 1) * 100)}%" if speed >= 1 else f"{int((speed - 1) * 100)}%"
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        
        # Collect audio chunks
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data
    
    def get_voices(self) -> list[Dict[str, Any]]:
        """Get available Edge TTS voices"""
        # Common voices - full list available via edge_tts.list_voices()
        return [
            {"id": "en-US-AriaNeural", "name": "Aria", "gender": "Female", "locale": "en-US"},
            {"id": "en-US-GuyNeural", "name": "Guy", "gender": "Male", "locale": "en-US"},
            {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "Female", "locale": "en-US"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia", "gender": "Female", "locale": "en-GB"},
            {"id": "en-AU-NatashaNeural", "name": "Natasha", "gender": "Female", "locale": "en-AU"},
        ]


class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs TTS provider (premium)"""
    
    def __init__(self, api_key: str, default_voice_id: Optional[str] = None):
        self.api_key = api_key
        self.default_voice_id = default_voice_id
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = None,
        speed: float = 1.0,
        model: str = "eleven_monolingual_v1",
        **kwargs
    ) -> bytes:
        try:
            from elevenlabs import generate, set_api_key
        except ImportError:
            raise RuntimeError("elevenlabs not installed. Run: pip install elevenlabs")
        
        set_api_key(self.api_key)
        
        voice_id = voice or self.default_voice_id
        if not voice_id:
            raise ValueError("No voice ID specified for ElevenLabs")
        
        audio = generate(
            text=text,
            voice=voice_id,
            model=model
        )
        
        return bytes(audio)
    
    def get_voices(self) -> list[Dict[str, Any]]:
        """Get available ElevenLabs voices"""
        try:
            from elevenlabs import voices, set_api_key
            set_api_key(self.api_key)
            
            voice_list = voices()
            return [
                {"id": v.voice_id, "name": v.name, "category": v.category}
                for v in voice_list
            ]
        except Exception:
            return []


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI TTS provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def synthesize(
        self, 
        text: str, 
        voice: str = "nova",
        speed: float = 1.0,
        model: str = "tts-1",
        **kwargs
    ) -> bytes:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx not installed. Run: pip install httpx")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": text,
                    "voice": voice,
                    "speed": speed,
                    "response_format": "mp3"
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.content
    
    def get_voices(self) -> list[Dict[str, Any]]:
        """Get available OpenAI voices"""
        return [
            {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
            {"id": "echo", "name": "Echo", "description": "Warm and engaging"},
            {"id": "fable", "name": "Fable", "description": "Expressive and dynamic"},
            {"id": "onyx", "name": "Onyx", "description": "Deep and authoritative"},
            {"id": "nova", "name": "Nova", "description": "Friendly and upbeat"},
            {"id": "shimmer", "name": "Shimmer", "description": "Clear and optimistic"},
        ]


class TTSManager:
    """
    Main TTS manager that handles provider selection and synthesis
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._providers: Dict[TTSProvider, BaseTTSProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers based on config"""
        # Edge TTS is always available (free)
        self._providers[TTSProvider.EDGE] = EdgeTTSProvider()
        
        # ElevenLabs if configured
        if self.config.elevenlabs_api_key:
            self._providers[TTSProvider.ELEVENLABS] = ElevenLabsTTSProvider(
                api_key=self.config.elevenlabs_api_key,
                default_voice_id=self.config.elevenlabs_voice_id
            )
        
        # OpenAI if configured
        if self.config.openai_api_key:
            self._providers[TTSProvider.OPENAI] = OpenAITTSProvider(
                api_key=self.config.openai_api_key
            )
    
    def get_provider(self, provider: Optional[TTSProvider] = None) -> BaseTTSProvider:
        """Get a TTS provider instance"""
        provider = provider or self.config.provider
        
        if provider not in self._providers:
            raise ValueError(f"Provider {provider.value} not available or not configured")
        
        return self._providers[provider]
    
    async def synthesize(
        self,
        text: str,
        provider: Optional[TTSProvider] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to convert to speech
            provider: TTS provider to use (default from config)
            voice: Voice ID (default from config)
            speed: Speech speed multiplier (default from config)
            **kwargs: Additional provider-specific options
            
        Returns:
            Audio bytes (MP3 format by default)
        """
        # Parse and remove TTS directives from text
        text, directive = self.parse_directives(text)
        
        # Check if TTS should be skipped
        if directive.skip:
            return b""
        
        # Apply directive overrides
        voice = directive.voice or voice or self.config.voice
        speed = directive.speed or speed or self.config.speed
        
        # Truncate if too long
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length] + "..."
        
        # Get provider and synthesize
        tts_provider = self.get_provider(provider)
        
        return await tts_provider.synthesize(
            text=text,
            voice=voice,
            speed=speed,
            **kwargs
        )
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Synthesize speech and save to file
        
        Returns:
            Path to the saved audio file
        """
        audio_data = await self.synthesize(text, **kwargs)
        
        if not output_path:
            suffix = f".{self.config.output_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                output_path = f.name
        
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return output_path
    
    def parse_directives(self, text: str) -> tuple[str, TTSDirective]:
        """
        Parse TTS directives from text
        
        Directives are in the format: [[tts:key=value,key2=value2]]
        Example: [[tts:voice=nova,speed=1.2]]
        
        Returns:
            Tuple of (cleaned text, parsed directive)
        """
        directive = TTSDirective()
        
        # Find and parse [[tts:...]] tags
        pattern = r'\[\[tts:([^\]]+)\]\]'
        matches = re.findall(pattern, text)
        
        for match in matches:
            pairs = match.split(',')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'voice':
                        directive.voice = value
                    elif key == 'speed':
                        try:
                            directive.speed = float(value)
                        except ValueError:
                            pass
                    elif key == 'emotion':
                        directive.emotion = value
                    elif key == 'skip' and value.lower() in ('true', '1', 'yes'):
                        directive.skip = True
        
        # Remove directive tags from text
        cleaned_text = re.sub(pattern, '', text).strip()
        
        return cleaned_text, directive
    
    def should_speak(self, is_voice_input: bool = False, has_directive: bool = False) -> bool:
        """
        Determine if a response should be spoken based on TTS mode
        
        Args:
            is_voice_input: Whether the input came from voice
            has_directive: Whether the response contains a TTS directive
        """
        if not self.config.enabled:
            return False
        
        mode = self.config.mode
        
        if mode == TTSMode.OFF:
            return False
        elif mode == TTSMode.ALWAYS:
            return True
        elif mode == TTSMode.INBOUND:
            return is_voice_input
        elif mode == TTSMode.TAGGED:
            return has_directive
        
        return False
    
    def get_available_voices(self, provider: Optional[TTSProvider] = None) -> list[Dict[str, Any]]:
        """Get list of available voices for a provider"""
        tts_provider = self.get_provider(provider)
        return tts_provider.get_voices()
    
    @classmethod
    def from_env(cls) -> 'TTSManager':
        """Create TTSManager from environment variables"""
        config = TTSConfig(
            enabled=os.getenv('GLTCH_TTS_ENABLED', 'false').lower() == 'true',
            provider=TTSProvider(os.getenv('GLTCH_TTS_PROVIDER', 'edge')),
            mode=TTSMode(os.getenv('GLTCH_TTS_MODE', 'off')),
            voice=os.getenv('GLTCH_TTS_VOICE', 'en-US-AriaNeural'),
            speed=float(os.getenv('GLTCH_TTS_SPEED', '1.0')),
            elevenlabs_api_key=os.getenv('ELEVENLABS_API_KEY'),
            elevenlabs_voice_id=os.getenv('ELEVENLABS_VOICE_ID'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_voice=os.getenv('OPENAI_TTS_VOICE', 'nova'),
        )
        return cls(config)
