"""
GLTCH Audio Module
Text-to-Speech and voice capabilities
"""

from .tts import (
    TTSManager, 
    TTSProvider, 
    TTSConfig, 
    TTSMode,
    TTSDirective
)
from .voice_wake import (
    VoiceWakeManager,
    VoiceWakeConfig,
    VoiceWakeEvent,
    VoiceWakeState
)
from .talk_mode import (
    TalkModeManager,
    TalkConfig,
    TalkSession,
    TalkPhase
)

__all__ = [
    # TTS
    'TTSManager',
    'TTSProvider', 
    'TTSConfig',
    'TTSMode',
    'TTSDirective',
    # Voice Wake
    'VoiceWakeManager',
    'VoiceWakeConfig',
    'VoiceWakeEvent',
    'VoiceWakeState',
    # Talk Mode
    'TalkModeManager',
    'TalkConfig',
    'TalkSession',
    'TalkPhase',
]
