"""
GLTCH Agent - Local-first, command-driven operator agent

Features:
- Multi-channel messaging (Discord, Telegram, Slack, WhatsApp, Signal, etc.)
- Personality system with emotions and moods
- Gamification with XP and ranks
- Text-to-Speech and Voice Wake
- Native apps for macOS, iOS, and Android
- Cron scheduling and webhooks
- Skills platform for extensibility
- DM pairing and sandboxed execution
- Multi-agent routing
- Crypto/blockchain integration
- AR mode overlay system
- Glitch visual effects
"""

__version__ = "0.3.0"
__author__ = "GLTCH Team"

from agent.core.agent import GltchAgent

# Audio features
from agent.audio import TTSManager, VoiceWakeManager, TalkModeManager

# Automation features
from agent.automation import CronScheduler, WebhookManager, SkillsManager

# Security features
from agent.security import PairingManager, SandboxManager, MultiAgentRouter

# Advanced tools
from agent.tools import CryptoAgent, ARMode, ar_mode, GlitchEffects, glitch_effects

__all__ = [
    # Core
    "GltchAgent",
    "__version__",
    
    # Audio
    "TTSManager",
    "VoiceWakeManager", 
    "TalkModeManager",
    
    # Automation
    "CronScheduler",
    "WebhookManager",
    "SkillsManager",
    
    # Security
    "PairingManager",
    "SandboxManager",
    "MultiAgentRouter",
    
    # Advanced Tools
    "CryptoAgent",
    "ARMode",
    "ar_mode",
    "GlitchEffects",
    "glitch_effects",
]
