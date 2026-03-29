"""
GLTCH Learner
Extracts patterns, preferences, and corrections from conversations
to build an operator profile that improves responses over time.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


PATTERNS_FILE = "learned_patterns.json"

DEFAULT_PATTERNS = {
    "preferences": [],     # [{type, value, confidence, first_seen, last_seen, count}]
    "corrections": [],     # [{original, corrected, context, confidence, first_seen, last_seen, count}]
    "workflows": [],       # [{name, steps, frequency, last_used}]
    "style": {
        "avg_response_length": None,   # "short" | "medium" | "long"
        "formality": None,             # "casual" | "neutral" | "formal"
        "topics": {},                  # topic -> mention_count
        "time_patterns": {},           # hour -> interaction_count
    },
    "stats": {
        "conversations_analyzed": 0,
        "last_analysis": None
    }
}

# Correction patterns in user messages
CORRECTION_PATTERNS = [
    # "don't say X, say Y"
    r"(?:don'?t|stop|quit)\s+(?:say(?:ing)?|us(?:e|ing)|call(?:ing)?)\s+[\"']?(.+?)[\"']?\s*[,;]\s*(?:say|use|call|it'?s)\s+[\"']?(.+?)[\"']?(?:\.|!|$)",
    # "X not Y"
    r"(?:it'?s|use)\s+[\"']?(.+?)[\"']?\s*(?:,\s*)?not\s+[\"']?(.+?)[\"']?(?:\.|!|$)",
    # "actually, X"
    r"(?:actually|no),?\s+(?:it'?s|it is|use)\s+[\"']?(.+?)[\"']?(?:\.|!|$)",
]

# Preference patterns in user messages
PREFERENCE_EXTRACT = [
    (r"(?:i |we )(?:always |usually |prefer to )?(?:use|prefer|like|want)\s+(.+?)(?:\s+(?:for|when|instead|over)\s+(.+?))?(?:\.|,|!|$)", "prefers"),
    (r"(?:i |we )(?:hate|dislike|don'?t like|avoid)\s+(.+?)(?:\.|,|!|$)", "dislikes"),
    (r"(?:my |our )(?:go-?to|default|favorite|fav)\s+(?:\w+\s+)?(?:is |= ?)(.+?)(?:\.|,|!|$)", "favorite"),
    (r"(?:make it|keep it|i want it)\s+(short|brief|detailed|verbose|minimal|concise)", "style"),
]

# Workflow detection: user repeatedly asks for multi-step processes
WORKFLOW_TRIGGERS = [
    "then", "after that", "next", "and then", "finally",
    "step 1", "step 2", "first", "second", "third",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Learner:
    """
    Learns operator patterns from conversations to build a profile.
    """

    def __init__(self, patterns_file: str = PATTERNS_FILE):
        self.patterns_file = patterns_file
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load learned patterns from disk."""
        if not os.path.exists(self.patterns_file):
            return json.loads(json.dumps(DEFAULT_PATTERNS))

        try:
            with open(self.patterns_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Forward-compat
            for k, v in DEFAULT_PATTERNS.items():
                if isinstance(v, dict):
                    data.setdefault(k, {})
                    for sk, sv in v.items():
                        data[k].setdefault(sk, sv)
                else:
                    data.setdefault(k, v if not isinstance(v, list) else [])
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_PATTERNS))

    def _save(self) -> None:
        """Save patterns to disk atomically."""
        tmp = self.patterns_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.patterns_file)

    # ── Analysis ──

    def analyze_conversation(
        self,
        user_message: str,
        assistant_response: str,
        operator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a conversation turn and extract learnable patterns.
        Returns summary of what was learned.
        """
        learned = {"corrections": [], "preferences": [], "style_updates": []}

        # 1. Extract corrections
        corrections = self.extract_corrections(user_message)
        for corr in corrections:
            self._add_correction(corr["original"], corr["corrected"], user_message)
            learned["corrections"].append(corr)

        # 2. Extract preferences
        preferences = self.extract_preferences(user_message)
        for pref in preferences:
            self._add_preference(pref["type"], pref["value"])
            learned["preferences"].append(pref)

        # 3. Track style signals
        style_updates = self._analyze_style(user_message, assistant_response)
        learned["style_updates"] = style_updates

        # 4. Track topic interests
        self._track_topics(user_message)

        # 5. Track time patterns
        hour = datetime.now().hour
        hour_key = str(hour)
        self.data["style"].setdefault("time_patterns", {})
        self.data["style"]["time_patterns"][hour_key] = \
            self.data["style"]["time_patterns"].get(hour_key, 0) + 1

        # Update stats
        self.data["stats"]["conversations_analyzed"] += 1
        self.data["stats"]["last_analysis"] = _now_iso()

        self._save()
        return learned

    def extract_corrections(self, user_message: str) -> List[Dict[str, str]]:
        """Extract correction patterns from user message."""
        corrections = []

        for pattern in CORRECTION_PATTERNS:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    corrections.append({
                        "original": match[1].strip() if len(match) > 1 else "",
                        "corrected": match[0].strip()
                    })
                elif isinstance(match, str):
                    corrections.append({
                        "original": "",
                        "corrected": match.strip()
                    })

        return corrections

    def extract_preferences(self, user_message: str) -> List[Dict[str, str]]:
        """Extract preference patterns from user message."""
        preferences = []

        for pattern, pref_type in PREFERENCE_EXTRACT:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                value = match[0].strip() if isinstance(match, tuple) else match.strip()
                if value and len(value) > 1 and len(value) < 80:
                    pref = {"type": pref_type, "value": value}
                    if isinstance(match, tuple) and len(match) > 1 and match[1]:
                        pref["context"] = match[1].strip()
                    preferences.append(pref)

        return preferences

    def _add_correction(self, original: str, corrected: str, context: str) -> None:
        """Add or update a correction pattern."""
        now = _now_iso()

        for corr in self.data["corrections"]:
            if corr["corrected"].lower() == corrected.lower():
                corr["count"] = corr.get("count", 1) + 1
                corr["last_seen"] = now
                corr["confidence"] = min(1.0, corr.get("confidence", 0.5) + 0.1)
                self._save()
                return

        self.data["corrections"].append({
            "original": original,
            "corrected": corrected,
            "context": context[:100],
            "confidence": 0.6,
            "first_seen": now,
            "last_seen": now,
            "count": 1
        })
        self._save()

    def _add_preference(self, pref_type: str, value: str) -> None:
        """Add or update a preference."""
        now = _now_iso()

        for pref in self.data["preferences"]:
            if pref["value"].lower() == value.lower() and pref["type"] == pref_type:
                pref["count"] = pref.get("count", 1) + 1
                pref["last_seen"] = now
                pref["confidence"] = min(1.0, pref.get("confidence", 0.5) + 0.1)
                self._save()
                return

        self.data["preferences"].append({
            "type": pref_type,
            "value": value,
            "confidence": 0.5,
            "first_seen": now,
            "last_seen": now,
            "count": 1
        })
        self._save()

    def _analyze_style(self, user_message: str, assistant_response: str) -> List[str]:
        """Analyze communication style signals."""
        updates = []

        # Response length preference detection
        word_count = len(user_message.split())
        if word_count < 5:
            self.data["style"]["avg_response_length"] = "short"
            updates.append("short_messages")
        elif word_count > 50:
            self.data["style"]["avg_response_length"] = "long"
            updates.append("detailed_messages")

        # Formality detection
        casual_markers = ["lol", "lmao", "bruh", "nah", "idk", "tbh", "imo", "pls", "plz", "u ", "ur "]
        formal_markers = ["please", "could you", "would you", "i would like", "kindly"]

        msg_lower = user_message.lower()
        casual_count = sum(1 for m in casual_markers if m in msg_lower)
        formal_count = sum(1 for m in formal_markers if m in msg_lower)

        if casual_count > formal_count:
            self.data["style"]["formality"] = "casual"
            updates.append("casual_style")
        elif formal_count > casual_count:
            self.data["style"]["formality"] = "formal"
            updates.append("formal_style")

        return updates

    def _track_topics(self, user_message: str) -> None:
        """Track topics the operator is interested in."""
        topic_keywords = {
            "security": ["security", "hack", "pentest", "vuln", "exploit", "nmap", "scan"],
            "web_dev": ["react", "next", "vite", "html", "css", "frontend", "backend", "api"],
            "devops": ["docker", "deploy", "nginx", "systemd", "ci/cd", "pipeline"],
            "crypto": ["wallet", "token", "blockchain", "web3", "contract", "eth"],
            "ai_ml": ["model", "training", "llm", "neural", "ai", "machine learning", "gpu"],
            "networking": ["network", "dns", "ip", "port", "firewall", "vpn", "ssh"],
            "coding": ["code", "debug", "refactor", "test", "function", "class", "module"],
        }

        msg_lower = user_message.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                self.data["style"].setdefault("topics", {})
                self.data["style"]["topics"][topic] = \
                    self.data["style"]["topics"].get(topic, 0) + 1

    # ── Profile Generation ──

    def get_operator_profile(self) -> str:
        """
        Build compact operator profile string for system prompt injection.
        Only includes patterns with sufficient confidence.
        """
        lines = []

        # High-confidence corrections
        strong_corrections = [
            c for c in self.data.get("corrections", [])
            if c.get("confidence", 0) >= 0.6
        ]
        if strong_corrections:
            lines.append("OPERATOR CORRECTIONS:")
            for corr in strong_corrections[:5]:
                if corr.get("original"):
                    lines.append(f"- Say \"{corr['corrected']}\" not \"{corr['original']}\"")
                else:
                    lines.append(f"- Remember: \"{corr['corrected']}\"")

        # Strong preferences
        strong_prefs = [
            p for p in self.data.get("preferences", [])
            if p.get("confidence", 0) >= 0.5
        ]
        if strong_prefs:
            lines.append("OPERATOR PREFERENCES:")
            for pref in strong_prefs[:8]:
                ptype = pref["type"]
                value = pref["value"]
                if ptype == "prefers":
                    lines.append(f"- Prefers: {value}")
                elif ptype == "dislikes":
                    lines.append(f"- Avoid: {value}")
                elif ptype == "favorite":
                    lines.append(f"- Go-to: {value}")
                elif ptype == "style":
                    lines.append(f"- Style: {value}")

        # Style notes
        style = self.data.get("style", {})
        style_notes = []
        if style.get("formality"):
            style_notes.append(f"tone={style['formality']}")
        if style.get("avg_response_length"):
            style_notes.append(f"msgs={style['avg_response_length']}")

        # Top topics
        topics = style.get("topics", {})
        if topics:
            top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]
            topic_str = ", ".join(t[0] for t in top_topics)
            style_notes.append(f"interests={topic_str}")

        if style_notes:
            lines.append(f"OPERATOR STYLE: {' | '.join(style_notes)}")

        return "\n".join(lines)

    # ── Decay ──

    def decay_old_patterns(self, days_threshold: int = 30) -> int:
        """
        Reduce confidence on patterns not seen recently.
        Returns count of decayed patterns.
        """
        decayed = 0
        cutoff = datetime.now().timestamp() - (days_threshold * 86400)

        for collection_name in ["corrections", "preferences"]:
            to_remove = []
            for i, item in enumerate(self.data.get(collection_name, [])):
                try:
                    last_seen = datetime.fromisoformat(item.get("last_seen", "")).timestamp()
                    if last_seen < cutoff:
                        item["confidence"] = max(0, item.get("confidence", 0.5) - 0.2)
                        decayed += 1
                        if item["confidence"] <= 0:
                            to_remove.append(i)
                except (ValueError, TypeError):
                    continue

            # Remove dead patterns
            for i in reversed(to_remove):
                self.data[collection_name].pop(i)

        if decayed:
            self._save()

        return decayed

    # ── Stats ──

    def get_stats(self) -> Dict[str, Any]:
        """Get learner statistics."""
        return {
            "preferences": len(self.data.get("preferences", [])),
            "corrections": len(self.data.get("corrections", [])),
            "workflows": len(self.data.get("workflows", [])),
            "top_topics": dict(
                sorted(
                    self.data.get("style", {}).get("topics", {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            ),
            "conversations_analyzed": self.data["stats"]["conversations_analyzed"],
            "last_analysis": self.data["stats"]["last_analysis"]
        }
