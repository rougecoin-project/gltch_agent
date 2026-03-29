"""
GLTCH Knowledge Graph
Persistent entity/relationship memory that grows across conversations.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple


KG_FILE = "knowledge_graph.json"

DEFAULT_KG = {
    "entities": {},      # id -> {type, name, aliases, first_seen, last_seen, mentions, meta}
    "relations": [],     # [{source, target, type, weight, first_seen, last_seen}]
    "stats": {
        "total_extractions": 0,
        "last_extraction": None
    }
}

# Entity types for classification
ENTITY_TYPES = {
    "project": ["repo", "repository", "codebase", "app", "project", "package", "module", "site", "platform"],
    "person": ["user", "operator", "dev", "developer", "admin", "author", "creator"],
    "tool": ["tool", "framework", "library", "sdk", "cli", "editor", "ide", "compiler"],
    "language": ["python", "javascript", "typescript", "rust", "go", "bash", "c", "c++", "java", "ruby", "php"],
    "service": ["api", "server", "database", "cloud", "docker", "kubernetes", "nginx", "redis", "postgres"],
    "url": [],  # detected via regex
    "preference": [],  # detected via pattern matching
    "concept": [],  # fallback
}

# Patterns that indicate preferences
PREFERENCE_PATTERNS = [
    (r"(?:i |we )(?:prefer|like|use|want|always use)\s+(.+?)(?:\.|,|$)", "prefers"),
    (r"(?:don'?t|never|avoid)\s+(?:use|do|want)\s+(.+?)(?:\.|,|$)", "avoids"),
    (r"(?:switch|change|move)\s+(?:to|from)\s+(.+?)(?:\.|,|$)", "switched_to"),
]

# Relation patterns
RELATION_PATTERNS = [
    (r"(\w+)\s+(?:uses?|runs?|depends?\s+on|built\s+with)\s+(\w+)", "uses"),
    (r"(\w+)\s+(?:is\s+(?:part|a\s+module)\s+of|belongs?\s+to)\s+(\w+)", "part_of"),
    (r"(\w+)\s+(?:connects?\s+to|integrates?\s+with|talks?\s+to)\s+(\w+)", "connects_to"),
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _entity_id(name: str) -> str:
    """Generate a stable ID from a name."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


class KnowledgeGraph:
    """
    Persistent knowledge graph that extracts and stores entities
    and relationships from conversations.
    """

    def __init__(self, kg_file: str = KG_FILE):
        self.kg_file = kg_file
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load knowledge graph from disk."""
        if not os.path.exists(self.kg_file):
            return json.loads(json.dumps(DEFAULT_KG))  # deep copy

        try:
            with open(self.kg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Forward-compat
            for k, v in DEFAULT_KG.items():
                data.setdefault(k, v if not isinstance(v, dict) else v.copy())
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_KG))

    def _save(self) -> None:
        """Save knowledge graph to disk atomically."""
        tmp = self.kg_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.kg_file)

    # ── Entity Operations ──

    def add_entity(
        self,
        name: str,
        entity_type: str = "concept",
        aliases: Optional[List[str]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add or update an entity. Returns entity ID."""
        eid = _entity_id(name)
        now = _now_iso()

        if eid in self.data["entities"]:
            # Update existing
            entity = self.data["entities"][eid]
            entity["last_seen"] = now
            entity["mentions"] = entity.get("mentions", 0) + 1
            if aliases:
                existing = set(entity.get("aliases", []))
                existing.update(aliases)
                entity["aliases"] = list(existing)
            if meta:
                entity.setdefault("meta", {}).update(meta)
        else:
            # Create new
            self.data["entities"][eid] = {
                "type": entity_type,
                "name": name,
                "aliases": aliases or [],
                "first_seen": now,
                "last_seen": now,
                "mentions": 1,
                "meta": meta or {}
            }

        self._save()
        return eid

    def get_entity(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by name or ID."""
        eid = _entity_id(name_or_id)
        if eid in self.data["entities"]:
            return self.data["entities"][eid]

        # Search aliases
        for entity in self.data["entities"].values():
            if name_or_id.lower() in [a.lower() for a in entity.get("aliases", [])]:
                return entity
        return None

    def remove_entity(self, name_or_id: str) -> bool:
        """Remove an entity and its relations."""
        eid = _entity_id(name_or_id)
        if eid not in self.data["entities"]:
            return False

        del self.data["entities"][eid]
        # Remove related relations
        self.data["relations"] = [
            r for r in self.data["relations"]
            if r["source"] != eid and r["target"] != eid
        ]
        self._save()
        return True

    # ── Relation Operations ──

    def add_relation(
        self,
        source: str,
        target: str,
        relation_type: str = "related_to"
    ) -> None:
        """Add or strengthen a relationship between entities."""
        src_id = _entity_id(source)
        tgt_id = _entity_id(target)
        now = _now_iso()

        # Check if relation exists
        for rel in self.data["relations"]:
            if rel["source"] == src_id and rel["target"] == tgt_id and rel["type"] == relation_type:
                rel["weight"] = rel.get("weight", 1) + 1
                rel["last_seen"] = now
                self._save()
                return

        # Create new
        self.data["relations"].append({
            "source": src_id,
            "target": tgt_id,
            "type": relation_type,
            "weight": 1,
            "first_seen": now,
            "last_seen": now
        })
        self._save()

    def get_relations(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relations for an entity."""
        eid = _entity_id(entity_name)
        return [
            r for r in self.data["relations"]
            if r["source"] == eid or r["target"] == eid
        ]

    # ── Extraction ──

    def extract_from_conversation(
        self,
        user_message: str,
        assistant_response: str,
        operator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from a conversation turn.
        Returns summary of what was extracted.
        """
        extracted = {"entities": [], "relations": [], "preferences": []}
        combined = f"{user_message} {assistant_response}"

        # 1. Extract URLs
        urls = re.findall(r'https?://[^\s\)\"\']+', combined)
        for url in urls:
            domain = url.split("//")[1].split("/")[0] if "//" in url else url
            eid = self.add_entity(domain, "url", meta={"url": url})
            extracted["entities"].append(domain)

        # 2. Extract known language mentions
        for lang in ENTITY_TYPES["language"]:
            pattern = r'\b' + re.escape(lang) + r'\b'
            if re.search(pattern, combined, re.IGNORECASE):
                self.add_entity(lang, "language")
                extracted["entities"].append(lang)

        # 3. Extract file paths (projects/tools)
        paths = re.findall(r'(?:[\w/\\.-]+\.(?:py|ts|js|rs|go|json|yaml|yml|toml|md|sh|css|html))', combined)
        for path in paths[:5]:  # limit
            # Extract potential project from path
            parts = path.replace("\\", "/").split("/")
            if len(parts) > 1:
                project = parts[0] if parts[0] not in (".", "..") else parts[1] if len(parts) > 1 else None
                if project and len(project) > 2:
                    self.add_entity(project, "project")
                    extracted["entities"].append(project)

        # 4. Extract preferences from user message
        for pattern, pref_type in PREFERENCE_PATTERNS:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 2 and len(match) < 60:
                    self.add_entity(match, "preference", meta={"preference_type": pref_type})
                    extracted["preferences"].append({"type": pref_type, "value": match})

        # 5. Extract tool/service names from common patterns
        tool_patterns = [
            r'(?:using|install|pip install|npm install|import)\s+(\w+)',
            r'(?:docker|redis|postgres|nginx|ollama|vite|react|next\.?js)\b',
        ]
        for pattern in tool_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match) > 2 and match.lower() not in ("the", "and", "for", "from", "with"):
                    entity_type = "tool"
                    if match.lower() in [s.lower() for s in ENTITY_TYPES["service"]]:
                        entity_type = "service"
                    self.add_entity(match, entity_type)
                    extracted["entities"].append(match)

        # 6. Extract relations
        for pattern, rel_type in RELATION_PATTERNS:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for src, tgt in matches:
                if len(src) > 2 and len(tgt) > 2:
                    self.add_relation(src, tgt, rel_type)
                    extracted["relations"].append({"source": src, "target": tgt, "type": rel_type})

        # 7. Link to operator
        if operator:
            op_id = self.add_entity(operator, "person")
            for ent_name in extracted["entities"][:5]:
                self.add_relation(operator, ent_name, "mentioned")

        # Update stats
        self.data["stats"]["total_extractions"] += 1
        self.data["stats"]["last_extraction"] = _now_iso()
        self._save()

        return extracted

    # ── Context Generation ──

    def get_relevant_context(
        self,
        user_message: str,
        max_entities: int = 10
    ) -> str:
        """
        Build compact context string from knowledge graph
        relevant to the current user message.
        """
        if not self.data["entities"]:
            return ""

        words = set(user_message.lower().split())
        scored: List[Tuple[float, str, Dict]] = []

        for eid, entity in self.data["entities"].items():
            score = 0.0
            name_lower = entity["name"].lower()

            # Direct mention in message
            if name_lower in user_message.lower():
                score += 10.0
            # Word overlap
            name_words = set(name_lower.split("_"))
            overlap = words & name_words
            if overlap:
                score += len(overlap) * 3.0
            # Alias match
            for alias in entity.get("aliases", []):
                if alias.lower() in user_message.lower():
                    score += 5.0
            # Recency bonus
            mentions = entity.get("mentions", 1)
            score += min(mentions * 0.5, 3.0)

            if score > 0:
                scored.append((score, eid, entity))

        # Sort by score, take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_entities]

        if not top:
            return ""

        # Build compact context
        lines = ["KNOWLEDGE (from past conversations):"]
        for _, eid, entity in top:
            etype = entity["type"]
            name = entity["name"]
            meta_str = ""
            if entity.get("meta"):
                meta_items = [f"{k}={v}" for k, v in list(entity["meta"].items())[:3]]
                meta_str = f" ({', '.join(meta_items)})"
            lines.append(f"- [{etype}] {name}{meta_str}")

            # Include relevant relations
            relations = self.get_relations(name)
            for rel in relations[:3]:
                other = rel["target"] if rel["source"] == eid else rel["source"]
                other_entity = self.data["entities"].get(other, {})
                other_name = other_entity.get("name", other)
                lines.append(f"  → {rel['type']} {other_name}")

        return "\n".join(lines)

    # ── Search & List ──

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search entities by name, alias, or type."""
        query_lower = query.lower()
        results = []

        for eid, entity in self.data["entities"].items():
            if query_lower in entity["name"].lower():
                results.append({"id": eid, **entity})
                continue
            if query_lower in entity.get("type", ""):
                results.append({"id": eid, **entity})
                continue
            for alias in entity.get("aliases", []):
                if query_lower in alias.lower():
                    results.append({"id": eid, **entity})
                    break

        return results

    def list_entities(self, entity_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List entities, optionally filtered by type."""
        entities = []
        for eid, entity in self.data["entities"].items():
            if entity_type and entity.get("type") != entity_type:
                continue
            entities.append({"id": eid, **entity})

        # Sort by mentions (most referenced first)
        entities.sort(key=lambda e: e.get("mentions", 0), reverse=True)
        return entities[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        type_counts: Dict[str, int] = {}
        for entity in self.data["entities"].values():
            etype = entity.get("type", "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1

        return {
            "total_entities": len(self.data["entities"]),
            "total_relations": len(self.data["relations"]),
            "entity_types": type_counts,
            "total_extractions": self.data["stats"]["total_extractions"],
            "last_extraction": self.data["stats"]["last_extraction"]
        }

    def merge(self, entity1: str, entity2: str) -> bool:
        """Merge entity2 into entity1 (combine mentions, aliases, relations)."""
        id1 = _entity_id(entity1)
        id2 = _entity_id(entity2)

        if id1 not in self.data["entities"] or id2 not in self.data["entities"]:
            return False

        e1 = self.data["entities"][id1]
        e2 = self.data["entities"][id2]

        # Merge aliases
        aliases = set(e1.get("aliases", []))
        aliases.add(e2["name"])
        aliases.update(e2.get("aliases", []))
        e1["aliases"] = list(aliases)

        # Merge mentions
        e1["mentions"] = e1.get("mentions", 0) + e2.get("mentions", 0)

        # Merge meta
        e1.setdefault("meta", {}).update(e2.get("meta", {}))

        # Repoint relations
        for rel in self.data["relations"]:
            if rel["source"] == id2:
                rel["source"] = id1
            if rel["target"] == id2:
                rel["target"] = id1

        # Remove duplicated self-relations
        self.data["relations"] = [
            r for r in self.data["relations"]
            if r["source"] != r["target"]
        ]

        # Delete entity2
        del self.data["entities"][id2]
        self._save()
        return True
