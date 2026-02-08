"""
GLTCH Effects Engine
Unique visual and audio glitch effects for responses
"""

import random
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class GlitchType(Enum):
    """Types of glitch effects"""
    TEXT_CORRUPT = "text_corrupt"
    ZALGO = "zalgo"
    MATRIX = "matrix"
    CYBERPUNK = "cyberpunk"
    VAPORWAVE = "vaporwave"
    REDACTED = "redacted"
    BINARY = "binary"
    HACKER = "hacker"


class GlitchIntensity(Enum):
    """Glitch effect intensity"""
    SUBTLE = "subtle"
    MEDIUM = "medium"
    HEAVY = "heavy"
    MAXIMUM = "maximum"


@dataclass
class GlitchConfig:
    """Glitch effects configuration"""
    enabled: bool = True
    default_intensity: GlitchIntensity = GlitchIntensity.SUBTLE
    auto_glitch_probability: float = 0.05  # 5% chance of random glitch
    preserve_readability: bool = True


class GlitchEffects:
    """
    GLTCH's signature visual effects engine
    
    Applies cyberpunk-style glitch effects to text:
    - Zalgo text corruption
    - Matrix-style encoding
    - Cyberpunk aesthetics
    - Hacker-style l33t speak
    - Redacted/classified effects
    """
    
    def __init__(self, config: Optional[GlitchConfig] = None):
        self.config = config or GlitchConfig()
        
        # Character sets
        self._zalgo_up = [
            '\u030d', '\u030e', '\u0304', '\u0305', '\u033f', 
            '\u0311', '\u0306', '\u0310', '\u0352', '\u0357',
            '\u0351', '\u0307', '\u0308', '\u030a', '\u0342'
        ]
        self._zalgo_down = [
            '\u0316', '\u0317', '\u0318', '\u0319', '\u031c',
            '\u031d', '\u031e', '\u031f', '\u0320', '\u0324',
            '\u0325', '\u0326', '\u0329', '\u032a', '\u032b'
        ]
        self._zalgo_mid = [
            '\u0315', '\u031b', '\u0340', '\u0341', '\u0358',
            '\u0321', '\u0322', '\u0327', '\u0328', '\u0334',
            '\u0335', '\u0336', '\u034f', '\u035c', '\u035d'
        ]
        
        self._matrix_chars = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
        
        self._leet_map = {
            'a': ['4', '@', 'Λ'],
            'b': ['8', 'ß', '|3'],
            'c': ['(', '<', '{'],
            'e': ['3', '€', 'ë'],
            'g': ['6', '9', '&'],
            'h': ['#', '|-|', '}{'],
            'i': ['1', '!', '|'],
            'l': ['1', '|', '/'],
            'o': ['0', '()', '[]'],
            's': ['5', '$', '§'],
            't': ['7', '+', '†'],
            'z': ['2', '7_', '>_'],
        }
        
        self._vaporwave_map = str.maketrans(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ'
        )
    
    def apply(
        self,
        text: str,
        glitch_type: GlitchType,
        intensity: Optional[GlitchIntensity] = None
    ) -> str:
        """Apply glitch effect to text"""
        if not self.config.enabled:
            return text
        
        intensity = intensity or self.config.default_intensity
        
        effects = {
            GlitchType.TEXT_CORRUPT: self._corrupt_text,
            GlitchType.ZALGO: self._zalgo,
            GlitchType.MATRIX: self._matrix,
            GlitchType.CYBERPUNK: self._cyberpunk,
            GlitchType.VAPORWAVE: self._vaporwave,
            GlitchType.REDACTED: self._redacted,
            GlitchType.BINARY: self._binary,
            GlitchType.HACKER: self._hacker,
        }
        
        effect_func = effects.get(glitch_type, lambda t, i: t)
        return effect_func(text, intensity)
    
    def auto_glitch(self, text: str) -> str:
        """Randomly apply glitch effect based on probability"""
        if not self.config.enabled:
            return text
        
        if random.random() < self.config.auto_glitch_probability:
            glitch_type = random.choice(list(GlitchType))
            intensity = GlitchIntensity.SUBTLE  # Keep auto-glitches subtle
            return self.apply(text, glitch_type, intensity)
        
        return text
    
    def _corrupt_text(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply text corruption effect"""
        corruption_chars = '░▒▓█▀▄■□▪▫'
        rates = {
            GlitchIntensity.SUBTLE: 0.02,
            GlitchIntensity.MEDIUM: 0.05,
            GlitchIntensity.HEAVY: 0.15,
            GlitchIntensity.MAXIMUM: 0.30,
        }
        rate = rates.get(intensity, 0.02)
        
        result = []
        for char in text:
            if random.random() < rate and char.strip():
                result.append(random.choice(corruption_chars))
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _zalgo(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply Zalgo text effect"""
        counts = {
            GlitchIntensity.SUBTLE: (1, 2),
            GlitchIntensity.MEDIUM: (2, 4),
            GlitchIntensity.HEAVY: (4, 8),
            GlitchIntensity.MAXIMUM: (8, 16),
        }
        min_count, max_count = counts.get(intensity, (1, 2))
        
        result = []
        for char in text:
            result.append(char)
            if char.strip():
                # Add combining characters
                for zalgo_set in [self._zalgo_up, self._zalgo_mid, self._zalgo_down]:
                    count = random.randint(min_count, max_count)
                    for _ in range(count):
                        result.append(random.choice(zalgo_set))
        
        return ''.join(result)
    
    def _matrix(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply Matrix-style effect"""
        rates = {
            GlitchIntensity.SUBTLE: 0.1,
            GlitchIntensity.MEDIUM: 0.25,
            GlitchIntensity.HEAVY: 0.5,
            GlitchIntensity.MAXIMUM: 0.8,
        }
        rate = rates.get(intensity, 0.1)
        
        result = []
        for char in text:
            if random.random() < rate and char.isalpha():
                result.append(random.choice(self._matrix_chars))
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _cyberpunk(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply cyberpunk aesthetic"""
        # Combine multiple effects
        prefixes = ['[SYS]', '> ', ':: ', '// ', '/* ']
        suffixes = [' _', ' |', ' ▌', ' ░']
        decorators = ['▓', '░', '▒', '█', '◢', '◣', '◤', '◥']
        
        if intensity in (GlitchIntensity.HEAVY, GlitchIntensity.MAXIMUM):
            prefix = random.choice(prefixes)
            suffix = random.choice(suffixes)
            text = f"{prefix}{text}{suffix}"
        
        if intensity == GlitchIntensity.MAXIMUM:
            text = f"{random.choice(decorators)} {text} {random.choice(decorators)}"
        
        # Apply partial leet speak
        text = self._hacker(text, GlitchIntensity.SUBTLE)
        
        return text
    
    def _vaporwave(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply vaporwave aesthetic"""
        # Convert to fullwidth
        text = text.translate(self._vaporwave_map)
        
        if intensity in (GlitchIntensity.MEDIUM, GlitchIntensity.HEAVY, GlitchIntensity.MAXIMUM):
            # Add spacing
            text = ' '.join(text)
        
        if intensity == GlitchIntensity.MAXIMUM:
            # Add aesthetic decorations
            text = f"☆ﾟ.*･｡ﾟ {text} ﾟ｡･*. ☆"
        
        return text
    
    def _redacted(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply redacted/classified effect"""
        word_rates = {
            GlitchIntensity.SUBTLE: 0.1,
            GlitchIntensity.MEDIUM: 0.25,
            GlitchIntensity.HEAVY: 0.5,
            GlitchIntensity.MAXIMUM: 0.75,
        }
        rate = word_rates.get(intensity, 0.1)
        
        words = text.split()
        result = []
        
        for word in words:
            if random.random() < rate:
                # Redact the word
                if len(word) > 2:
                    result.append('█' * len(word))
                else:
                    result.append('[REDACTED]')
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def _binary(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply binary encoding effect"""
        rates = {
            GlitchIntensity.SUBTLE: 0.05,
            GlitchIntensity.MEDIUM: 0.15,
            GlitchIntensity.HEAVY: 0.3,
            GlitchIntensity.MAXIMUM: 0.5,
        }
        rate = rates.get(intensity, 0.05)
        
        result = []
        for char in text:
            if random.random() < rate and char.isalpha():
                binary = format(ord(char), '08b')
                result.append(binary)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _hacker(self, text: str, intensity: GlitchIntensity) -> str:
        """Apply l33t speak effect"""
        rates = {
            GlitchIntensity.SUBTLE: 0.1,
            GlitchIntensity.MEDIUM: 0.3,
            GlitchIntensity.HEAVY: 0.6,
            GlitchIntensity.MAXIMUM: 0.9,
        }
        rate = rates.get(intensity, 0.1)
        
        result = []
        for char in text:
            lower_char = char.lower()
            if lower_char in self._leet_map and random.random() < rate:
                replacement = random.choice(self._leet_map[lower_char])
                result.append(replacement)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def glitch_signature(self) -> str:
        """Generate a glitchy signature"""
        signatures = [
            "「 ＧＬＴＣＨ 」",
            "░▒▓ GLTCH ▓▒░",
            "⟦ G̷L̷T̷C̷H̷ ⟧",
            "〔 gltch_agent 〕",
            "▌│█│▌│▌GLTCH▌│▌│█│▌",
            "◢◤ GLTCH ◥◣",
        ]
        return random.choice(signatures)
    
    def wrap_response(
        self,
        response: str,
        mood: Optional[str] = None,
        add_signature: bool = False
    ) -> str:
        """Wrap response with glitch aesthetic"""
        # Apply subtle auto-glitch
        response = self.auto_glitch(response)
        
        # Add mood-based styling
        if mood == "mischievous":
            response = self._cyberpunk(response, GlitchIntensity.SUBTLE)
        elif mood == "creative":
            # Light vaporwave touch
            pass
        
        if add_signature:
            response = f"{response}\n\n{self.glitch_signature()}"
        
        return response


# Global instance
glitch_effects = GlitchEffects()
