"""
GLTCH Session Manager
Multi-user session management for gateway integration.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List


class SessionManager:
    """
    Manages multiple user sessions for multi-channel support.
    Each session has its own chat history and context.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        self._sessions: Dict[str, Dict[str, Any]] = {}
        os.makedirs(sessions_dir, exist_ok=True)
    
    def _session_file(self, session_id: str) -> str:
        """Get the file path for a session."""
        safe_id = session_id.replace(":", "_").replace("/", "_")
        return os.path.join(self.sessions_dir, f"{safe_id}.json")
    
    def get(self, session_id: str) -> Dict[str, Any]:
        """Get or create a session."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        session_file = self._session_file(session_id)
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
            except Exception:
                session = self._create_session(session_id)
        else:
            session = self._create_session(session_id)
        
        self._sessions[session_id] = session
        return session
    
    def _create_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new session."""
        return {
            "id": session_id,
            "created": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "chat_history": [],
            "context": {},
            "user": None,
            "channel": None
        }
    
    def save(self, session_id: str) -> None:
        """Save a session to disk."""
        if session_id not in self._sessions:
            return
        
        session = self._sessions[session_id]
        session["last_active"] = datetime.now().isoformat()
        
        session_file = self._session_file(session_id)
        tmp = session_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        os.replace(tmp, session_file)
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history."""
        session = self.get(session_id)
        session["chat_history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep last 20 messages
        session["chat_history"] = session["chat_history"][-20:]
        self.save(session_id)
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get chat history for LLM context."""
        session = self.get(session_id)
        history = session.get("chat_history", [])[-limit:]
        # Return in LLM format (role, content only)
        return [{"role": m["role"], "content": m["content"]} for m in history]
    
    def clear_history(self, session_id: str) -> None:
        """Clear a session's chat history."""
        if session_id in self._sessions:
            self._sessions[session_id]["chat_history"] = []
            self.save(session_id)
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        session_file = self._session_file(session_id)
        if os.path.exists(session_file):
            os.remove(session_file)
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with metadata."""
        sessions = []
        for filename in os.listdir(self.sessions_dir):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.sessions_dir, filename), "r") as f:
                    session = json.load(f)
                    sessions.append({
                        "id": session.get("id"),
                        "created": session.get("created"),
                        "last_active": session.get("last_active"),
                        "message_count": len(session.get("chat_history", []))
                    })
            except Exception:
                continue
        return sorted(sessions, key=lambda s: s.get("last_active", ""), reverse=True)
