"""
GLTCH Session Manager
Multi-user session management with ChatGPT-style conversation history.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class SessionManager:
    """
    Manages multiple conversation sessions.
    Each session has its own chat history, title, and context.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._active_session_id: Optional[str] = None
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
    
    def _create_session(self, session_id: str, title: str = None) -> Dict[str, Any]:
        """Create a new session."""
        return {
            "id": session_id,
            "title": title or "New Chat",
            "created": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "chat_history": [],
            "context": {},
            "user": None,
            "channel": None
        }
    
    def new_session(self, title: str = None) -> Dict[str, Any]:
        """Create a new conversation session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        session = self._create_session(session_id, title)
        self._sessions[session_id] = session
        self._active_session_id = session_id
        self.save(session_id)
        return session
    
    def get_active(self) -> Dict[str, Any]:
        """Get the currently active session, creating one if needed."""
        if not self._active_session_id:
            # Try to load most recent session
            sessions = self.list_sessions()
            if sessions:
                self._active_session_id = sessions[0]["id"]
            else:
                # Create new session
                session = self.new_session()
                return session
        return self.get(self._active_session_id)
    
    def set_active(self, session_id: str) -> bool:
        """Switch to a different session."""
        session_file = self._session_file(session_id)
        if os.path.exists(session_file) or session_id in self._sessions:
            self._active_session_id = session_id
            return True
        return False
    
    def get_active_id(self) -> Optional[str]:
        """Get the active session ID."""
        return self._active_session_id
    
    def rename(self, session_id: str, title: str) -> bool:
        """Rename a session."""
        session = self.get(session_id)
        if session:
            session["title"] = title
            self.save(session_id)
            return True
        return False
    
    def auto_title(self, session_id: str, first_message: str) -> str:
        """Generate a title from the first message."""
        # Take first 40 chars, clean up
        title = first_message[:40].strip()
        if len(first_message) > 40:
            title += "..."
        # Remove newlines
        title = title.replace("\n", " ")
        self.rename(session_id, title)
        return title
    
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
                    history = session.get("chat_history", [])
                    # Get preview from last message
                    preview = ""
                    if history:
                        last_msg = history[-1].get("content", "")
                        preview = last_msg[:50] + "..." if len(last_msg) > 50 else last_msg
                    
                    sessions.append({
                        "id": session.get("id"),
                        "title": session.get("title", "Untitled"),
                        "created": session.get("created"),
                        "last_active": session.get("last_active"),
                        "message_count": len(history),
                        "preview": preview
                    })
            except Exception:
                continue
        return sorted(sessions, key=lambda s: s.get("last_active", ""), reverse=True)
