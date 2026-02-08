"""
GLTCH Tools Module
File operations, shell commands, action parsing, and advanced features.
"""

from agent.tools.file_ops import file_write, file_append, file_read, file_ls
from agent.tools.shell import run_shell
from agent.tools.actions import parse_and_execute_actions, strip_thinking, verify_suggestions

# Advanced tools
from agent.tools.crypto_agent import CryptoAgent
from agent.tools.ar_mode import ARMode, ar_mode
from agent.tools.glitch_effects import GlitchEffects, glitch_effects, GlitchType, GlitchIntensity

__all__ = [
    # File operations
    "file_write", "file_append", "file_read", "file_ls",
    # Shell
    "run_shell",
    # Actions
    "parse_and_execute_actions", "strip_thinking", "verify_suggestions",
    # Crypto
    "CryptoAgent",
    # AR Mode
    "ARMode", "ar_mode",
    # Glitch Effects
    "GlitchEffects", "glitch_effects", "GlitchType", "GlitchIntensity",
]
