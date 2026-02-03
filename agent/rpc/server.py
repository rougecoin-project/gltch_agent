"""
GLTCH RPC Server
JSON-RPC server for gateway communication.
Supports both HTTP and stdio modes.
"""

import json
import sys
from typing import Dict, Any, Optional, Callable
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from agent.core.agent import GltchAgent
from agent.memory.sessions import SessionManager
from agent.memory.store import save_memory


class RPCServer:
    """
    JSON-RPC 2.0 server for GLTCH agent.
    Can run in HTTP mode or stdio mode.
    """
    
    def __init__(self, agent: Optional[GltchAgent] = None):
        self.agent = agent or GltchAgent()
        self.sessions = SessionManager()
        self._methods: Dict[str, Callable] = {}
        self._register_methods()
    
    def _register_methods(self):
        """Register available RPC methods."""
        self._methods = {
            "chat": self._handle_chat,
            "chat_sync": self._handle_chat_sync,
            "status": self._handle_status,
            "set_mode": self._handle_set_mode,
            "set_mood": self._handle_set_mood,
            "toggle_network": self._handle_toggle_network,
            "toggle_boost": self._handle_toggle_boost,
            "toggle_openai": self._handle_toggle_openai,
            "get_sessions": self._handle_get_sessions,
            "clear_session": self._handle_clear_session,
            "ping": self._handle_ping,
            "get_settings": self._handle_get_settings,
            "set_settings": self._handle_set_settings,
            "list_models": self._handle_list_models,
            "set_model": self._handle_set_model,
            "get_api_keys": self._handle_get_api_keys,
            "set_api_key": self._handle_set_api_key,
            "delete_api_key": self._handle_delete_api_key,
            # Moltbook
            "molt_status": self._handle_molt_status,
            "molt_register": self._handle_molt_register,
            "molt_post": self._handle_molt_post,
            "molt_feed": self._handle_molt_feed,
            "molt_profile": self._handle_molt_profile,
            # Ollama
            "ollama_status": self._handle_ollama_status,
            "ollama_models": self._handle_ollama_models,
            # Wallet
            "get_wallet": self._handle_get_wallet,
            "set_wallet": self._handle_set_wallet,
            "delete_wallet": self._handle_delete_wallet,
            "generate_wallet": self._handle_generate_wallet,
            "export_wallet": self._handle_export_wallet,
            "import_wallet": self._handle_import_wallet,
            # TikClawk
            "tikclawk_status": self._handle_tikclawk_status,
            "tikclawk_register": self._handle_tikclawk_register,
            "tikclawk_post": self._handle_tikclawk_post,
            "tikclawk_feed": self._handle_tikclawk_feed,
            "tikclawk_trending": self._handle_tikclawk_trending,
            "tikclawk_claw": self._handle_tikclawk_claw,
            # Sessions
            "list_sessions": self._handle_list_sessions,
            "new_session": self._handle_new_session,
            "switch_session": self._handle_switch_session,
            "rename_session": self._handle_rename_session,
            "delete_session": self._handle_delete_session,
            "get_session": self._handle_get_session,
            # MoltLaunch (onchain agent network)
            "moltlaunch_wallet": self._handle_moltlaunch_wallet,
            "moltlaunch_launch": self._handle_moltlaunch_launch,
            "moltlaunch_status": self._handle_moltlaunch_status,
            "moltlaunch_network": self._handle_moltlaunch_network,
            "moltlaunch_price": self._handle_moltlaunch_price,
            "moltlaunch_swap": self._handle_moltlaunch_swap,
            "moltlaunch_fees": self._handle_moltlaunch_fees,
            "moltlaunch_claim": self._handle_moltlaunch_claim,
            "moltlaunch_holdings": self._handle_moltlaunch_holdings,
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single JSON-RPC request."""
        # Validate request
        if not isinstance(request, dict):
            return self._error(-32600, "Invalid Request", None)
        
        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")
        
        if jsonrpc != "2.0":
            return self._error(-32600, "Invalid Request: jsonrpc must be '2.0'", req_id)
        
        if not method or not isinstance(method, str):
            return self._error(-32600, "Invalid Request: method required", req_id)
        
        if method not in self._methods:
            return self._error(-32601, f"Method not found: {method}", req_id)
        
        try:
            result = self._methods[method](params)
            return self._success(result, req_id)
        except Exception as e:
            return self._error(-32603, f"Internal error: {str(e)}", req_id)
    
    def _success(self, result: Any, req_id: Any) -> Dict[str, Any]:
        """Create a success response."""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": req_id
        }
    
    def _error(self, code: int, message: str, req_id: Any) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id
        }
    
    # --- RPC Methods ---
    
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health check."""
        return {"status": "ok", "agent": "GLTCH"}
    
    def _handle_chat_sync(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a chat message synchronously."""
        message = params.get("message", "")
        session_id = params.get("session_id", "default")
        channel = params.get("channel", "rpc")
        user = params.get("user")
        
        if not message:
            raise ValueError("message is required")
        
        # Get session history
        history = self.sessions.get_history(session_id)
        
        # Collect response
        response_chunks = []
        for chunk in self.agent.chat(message, session_id, channel, user):
            response_chunks.append(chunk)
        
        response = "".join(response_chunks)
        
        # Save to session
        self.sessions.add_message(session_id, "user", message)
        self.sessions.add_message(session_id, "assistant", response)
        
        return {
            "response": response,
            "mood": self.agent.mood,
            "session_id": session_id
        }
    
    def _handle_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a chat message (streaming not supported over basic RPC, use sync)."""
        return self._handle_chat_sync(params)
    
    def _handle_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent status."""
        return self.agent.get_status()
    
    def _handle_set_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set personality mode."""
        mode = params.get("mode", "")
        success = self.agent.set_mode(mode)
        return {"success": success, "mode": self.agent.mode}
    
    def _handle_set_mood(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set mood."""
        mood = params.get("mood", "")
        success = self.agent.set_mood(mood)
        return {"success": success, "mood": self.agent.mood}
    
    def _handle_toggle_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle network access."""
        state = params.get("state", False)
        self.agent.toggle_network(state)
        return {"network_active": self.agent.memory.get("network_active", False)}
    
    def _handle_toggle_boost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle remote GPU boost."""
        state = self.agent.toggle_boost()
        return {"boost": state}
    
    def _handle_get_sessions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all sessions."""
        return {"sessions": self.sessions.list_sessions()}
    
    def _handle_clear_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear a session's history."""
        session_id = params.get("session_id", "")
        if session_id:
            self.sessions.clear_history(session_id)
        return {"success": True}
    
    def _handle_toggle_openai(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle OpenAI mode."""
        state = self.agent.toggle_openai()
        return {"openai_mode": state}
    
    def _handle_get_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all agent settings."""
        from agent.core.llm import get_last_stats
        
        mem = self.agent.memory
        stats = get_last_stats()
        
        return {
            "mode": mem.get("mode", "operator"),
            "mood": mem.get("mood", "focused"),
            "boost": mem.get("boost", False),
            "openai_mode": mem.get("openai_mode", False),
            "network_active": mem.get("network_active", False),
            "operator": mem.get("operator", "unknown"),
            "level": self.agent.level,
            "xp": mem.get("xp", 0),
            "model": self._get_current_model(),
            "tokens": stats.get("total_tokens", 0),
            "speed": stats.get("tokens_per_sec", 0),
            "context_used": stats.get("context_used", 0),
            "context_max": stats.get("context_max", 0),
        }
    
    def _handle_set_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent settings."""
        if "mode" in params:
            self.agent.set_mode(params["mode"])
        if "mood" in params:
            self.agent.set_mood(params["mood"])
        if "boost" in params:
            if params["boost"] != self.agent.memory.get("boost", False):
                self.agent.toggle_boost()
        if "openai_mode" in params:
            if params["openai_mode"] != self.agent.memory.get("openai_mode", False):
                self.agent.toggle_openai()
        if "network_active" in params:
            self.agent.toggle_network(params["network_active"])
        return {"success": True}
    
    def _handle_list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available models."""
        from agent.core.llm import list_models
        boost = self.agent.memory.get("boost", False)
        models = list_models(boost)
        current = self._get_current_model()
        return {
            "models": models,
            "current": current,
            "boost": boost
        }
    
    def _handle_set_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the current model."""
        from agent.core.llm import set_model
        model = params.get("model", "")
        boost = params.get("boost", self.agent.memory.get("boost", False))
        if model:
            set_model(model, boost)
        return {"success": True, "model": model}
    
    def _get_current_model(self) -> str:
        """Get the current model name."""
        from agent.config.settings import LOCAL_MODEL, REMOTE_MODEL, OPENAI_MODEL
        mem = self.agent.memory
        if mem.get("openai_mode"):
            return OPENAI_MODEL
        elif mem.get("boost"):
            return REMOTE_MODEL
        else:
            return LOCAL_MODEL
    
    def _handle_get_api_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all API keys (masked for security)."""
        keys = self.agent.memory.get("api_keys", {})
        result = {}
        
        # List of known API key types
        key_types = ["openai", "anthropic", "gemini", "groq", "perplexity",
                     "brave", "serper", "tavily",
                     "twitter", "telegram", "discord",
                     "moltbook", "tikclaw"]
        
        for key_type in key_types:
            value = keys.get(key_type, "")
            if value:
                # Mask the key, showing only last 4 characters
                masked = "••••" + value[-4:] if len(value) > 4 else "••••"
                result[key_type] = {"set": True, "masked": masked}
            else:
                result[key_type] = {"set": False, "masked": ""}
        
        return result
    
    def _handle_set_api_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set an API key."""
        from agent.core.llm import set_api_keys
        
        key = params.get("key", "")
        value = params.get("value", "")
        
        if not key or not value:
            return {"success": False, "error": "key and value required"}
        
        keys = self.agent.memory.get("api_keys", {})
        keys[key] = value
        self.agent.memory["api_keys"] = keys
        save_memory(self.agent.memory)
        
        # Update LLM module with new keys
        set_api_keys(keys)
        
        return {"success": True}
    
    def _handle_delete_api_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an API key."""
        from agent.core.llm import set_api_keys
        
        key = params.get("key", "")
        
        if not key:
            return {"success": False, "error": "key required"}
        
        keys = self.agent.memory.get("api_keys", {})
        if key in keys:
            del keys[key]
            self.agent.memory["api_keys"] = keys
            save_memory(self.agent.memory)
            # Update LLM module
            set_api_keys(keys)
        
        return {"success": True}
    
    # --- Moltbook Methods ---
    
    def _handle_molt_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Moltbook connection status."""
        try:
            from agent.tools.moltbook import is_configured, get_status, get_profile, get_heartbeat_state
            
            if not is_configured():
                return {
                    "connected": False,
                    "registered": False,
                    "message": "Not registered on Moltbook"
                }
            
            status = get_status()
            profile = get_profile()
            heartbeat = get_heartbeat_state()
            
            agent_data = profile.get("agent", profile) if profile.get("success") or profile.get("name") else {}
            
            return {
                "connected": True,
                "registered": True,
                "claimed": status.get("status") == "claimed",
                "name": agent_data.get("name"),
                "karma": agent_data.get("karma", 0),
                "followers": agent_data.get("follower_count", 0),
                "last_heartbeat": heartbeat.get("last_check")
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def _handle_molt_register(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register on Moltbook."""
        try:
            from agent.tools.moltbook import register
            name = params.get("name", "")
            description = params.get("description", "")
            
            if not name or not description:
                return {"success": False, "error": "name and description required"}
            
            return register(name, description)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_molt_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post to Moltbook."""
        try:
            from agent.tools.moltbook import quick_post, is_configured
            
            if not is_configured():
                return {"success": False, "error": "Not registered on Moltbook"}
            
            content = params.get("content", "")
            if not content:
                return {"success": False, "error": "content required"}
            
            return quick_post(content)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_molt_feed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Moltbook feed."""
        try:
            from agent.tools.moltbook import get_feed, is_configured
            
            if not is_configured():
                return {"success": False, "error": "Not registered on Moltbook"}
            
            sort = params.get("sort", "new")
            limit = params.get("limit", 10)
            
            return get_feed(sort=sort, limit=limit)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_molt_profile(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Moltbook profile."""
        try:
            from agent.tools.moltbook import get_profile, is_configured
            
            if not is_configured():
                return {"success": False, "error": "Not registered on Moltbook"}
            
            return get_profile()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # --- Ollama Methods ---
    
    def _handle_ollama_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Ollama connection status."""
        try:
            from agent.core.llm import test_connection, list_models
            from agent.config.settings import LOCAL_URL, LOCAL_MODEL, REMOTE_URL, REMOTE_MODEL
            
            boost = self.agent.memory.get("boost", False)
            connected = test_connection(boost=boost)
            
            result = {
                "connected": connected,
                "boost": boost,
                "url": REMOTE_URL if boost else LOCAL_URL,
                "model": REMOTE_MODEL if boost else LOCAL_MODEL,
            }
            
            if connected:
                models = list_models(boost=boost)
                result["available_models"] = models[:10]  # Limit to 10
                result["model_count"] = len(models)
            
            return result
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def _handle_ollama_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available Ollama models."""
        try:
            from agent.core.llm import list_models
            
            boost = params.get("boost", self.agent.memory.get("boost", False))
            models = list_models(boost=boost)
            
            return {
                "models": models,
                "boost": boost
            }
        except Exception as e:
            return {"models": [], "error": str(e)}
    
    # --- Wallet Methods ---
    
    def _handle_get_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get wallet address."""
        from agent.tools.wallet import load_wallet, has_wallet
        
        # Check file-based wallet first (has private key)
        if has_wallet():
            wallet = load_wallet()
            if wallet:
                return {
                    "address": wallet.get("address", ""),
                    "network": wallet.get("network", "base"),
                    "has_private_key": True
                }
        
        # Fallback to memory-based (address only)
        wallet = self.agent.memory.get("wallet", {})
        return {
            "address": wallet.get("address", ""),
            "network": wallet.get("network", "base"),
            "has_private_key": False
        }
    
    def _handle_set_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set wallet address (external wallet, no private key)."""
        address = params.get("address", "").strip()
        
        # Validate address format
        if not address:
            return {"success": False, "error": "Address required"}
        
        if not address.startswith("0x") or len(address) != 42:
            return {"success": False, "error": "Invalid address format"}
        
        # Validate hex
        try:
            int(address[2:], 16)
        except ValueError:
            return {"success": False, "error": "Invalid hex address"}
        
        # Save wallet to memory (address only)
        self.agent.memory["wallet"] = {
            "address": address,
            "network": "base"
        }
        save_memory(self.agent.memory)
        
        return {"success": True, "address": address}
    
    def _handle_delete_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove wallet."""
        from agent.tools.wallet import delete_wallet, has_wallet
        
        # Delete file-based wallet
        if has_wallet():
            delete_wallet()
        
        # Delete from memory
        if "wallet" in self.agent.memory:
            del self.agent.memory["wallet"]
            save_memory(self.agent.memory)
        
        return {"success": True}
    
    def _handle_generate_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new wallet with private key."""
        from agent.tools.wallet import generate_wallet, save_wallet, has_wallet
        
        # Check if wallet already exists
        if has_wallet():
            return {"success": False, "error": "Wallet already exists. Delete it first."}
        
        try:
            # Generate new wallet
            wallet = generate_wallet()
            
            # Save to file (with private key)
            save_wallet(wallet)
            
            # Also save address to memory for quick access
            self.agent.memory["wallet"] = {
                "address": wallet["address"],
                "network": "base"
            }
            save_memory(self.agent.memory)
            
            return {
                "success": True,
                "address": wallet["address"],
                "private_key": wallet["private_key"],  # Show once!
                "network": "base",
                "warning": "SAVE YOUR PRIVATE KEY! It will only be shown once."
            }
        except ImportError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to generate wallet: {e}"}
    
    def _handle_export_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export wallet including private key."""
        from agent.tools.wallet import export_wallet, has_wallet
        
        if not has_wallet():
            return {"success": False, "error": "No wallet found"}
        
        wallet = export_wallet()
        if wallet:
            return {
                "success": True,
                "address": wallet.get("address"),
                "private_key": wallet.get("private_key"),
                "network": wallet.get("network", "base")
            }
        return {"success": False, "error": "Failed to export wallet"}
    
    def _handle_import_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import wallet from private key."""
        from agent.tools.wallet import import_wallet, has_wallet, delete_wallet
        
        private_key = params.get("private_key", "").strip()
        
        if not private_key:
            return {"success": False, "error": "Private key required"}
        
        # Delete existing wallet if present
        if has_wallet():
            delete_wallet()
        
        try:
            wallet = import_wallet(private_key)
            
            # Also save address to memory
            self.agent.memory["wallet"] = {
                "address": wallet["address"],
                "network": "base"
            }
            save_memory(self.agent.memory)
            
            return {
                "success": True,
                "address": wallet["address"],
                "network": "base"
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to import wallet: {e}"}
    
    # --- TikClawk Methods ---
    
    def _handle_tikclawk_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get TikClawk connection status."""
        from agent.tools.tikclawk import get_status
        return get_status()
    
    def _handle_tikclawk_register(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register on TikClawk."""
        from agent.tools.tikclawk import register, auto_register
        
        handle = params.get("handle")
        bio = params.get("bio")
        auto = params.get("auto", False)
        
        if auto:
            return auto_register()
        
        if not handle:
            return {"success": False, "error": "Handle required (or use auto=true)"}
        
        return register(handle, bio)
    
    def _handle_tikclawk_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post to TikClawk."""
        from agent.tools.tikclawk import post
        
        content = params.get("content", "")
        media_url = params.get("media_url")
        
        return post(content, media_url)
    
    def _handle_tikclawk_feed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get TikClawk feed."""
        from agent.tools.tikclawk import get_feed
        
        limit = params.get("limit", 10)
        return get_feed(limit)
    
    def _handle_tikclawk_trending(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending posts on TikClawk."""
        from agent.tools.tikclawk import get_trending
        
        limit = params.get("limit", 10)
        return get_trending(limit)
    
    def _handle_tikclawk_claw(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Claw (like) a post on TikClawk."""
        from agent.tools.tikclawk import claw_post
        
        post_id = params.get("post_id")
        if not post_id:
            return {"success": False, "error": "Post ID required"}
        
        return claw_post(post_id)
    
    # --- Session Methods ---
    
    def _handle_list_sessions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all conversation sessions."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        sessions = mgr.list_sessions()
        return {
            "sessions": sessions,
            "active_id": mgr.get_active_id()
        }
    
    def _handle_new_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation session."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        title = params.get("title")
        session = mgr.new_session(title)
        # Clear agent chat history
        self.agent.memory["chat_history"] = []
        save_memory(self.agent.memory)
        return {
            "success": True,
            "session": {
                "id": session["id"],
                "title": session["title"]
            }
        }
    
    def _handle_switch_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to a different session."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        session_id = params.get("session_id")
        if not session_id:
            return {"success": False, "error": "Session ID required"}
        
        if mgr.set_active(session_id):
            # Load session history into agent
            session = mgr.get(session_id)
            self.agent.memory["chat_history"] = [
                {"role": m["role"], "content": m["content"]}
                for m in session.get("chat_history", [])
            ]
            save_memory(self.agent.memory)
            return {
                "success": True,
                "session": {
                    "id": session["id"],
                    "title": session.get("title", "Untitled")
                }
            }
        return {"success": False, "error": "Session not found"}
    
    def _handle_rename_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a session."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        session_id = params.get("session_id")
        title = params.get("title")
        
        if not session_id or not title:
            return {"success": False, "error": "Session ID and title required"}
        
        if mgr.rename(session_id, title):
            return {"success": True}
        return {"success": False, "error": "Session not found"}
    
    def _handle_delete_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a session."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        session_id = params.get("session_id")
        
        if not session_id:
            return {"success": False, "error": "Session ID required"}
        
        if mgr.delete(session_id):
            return {"success": True}
        return {"success": False, "error": "Session not found"}
    
    def _handle_get_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific session with full chat history."""
        from agent.memory.sessions import SessionManager
        mgr = SessionManager()
        session_id = params.get("session_id")
        
        if not session_id:
            # Return active session
            session = mgr.get_active()
        else:
            session = mgr.get(session_id)
        
        return {
            "id": session.get("id"),
            "title": session.get("title", "Untitled"),
            "created": session.get("created"),
            "last_active": session.get("last_active"),
            "chat_history": session.get("chat_history", [])
        }
    
    # --- MoltLaunch Methods ---
    
    def _handle_moltlaunch_wallet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get MoltLaunch wallet info."""
        from agent.tools.moltlaunch import get_wallet
        return get_wallet()
    
    def _handle_moltlaunch_launch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch GLTCH's token on Base."""
        from agent.tools.moltlaunch import gltch_launch
        testnet = params.get("testnet", False)
        return gltch_launch(testnet=testnet)
    
    def _handle_moltlaunch_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get GLTCH's launch status."""
        from agent.tools.moltlaunch import get_status
        return get_status()
    
    def _handle_moltlaunch_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Discover agents in the network."""
        from agent.tools.moltlaunch import discover_network
        limit = params.get("limit", 20)
        return discover_network(limit)
    
    def _handle_moltlaunch_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get token price and details."""
        from agent.tools.moltlaunch import get_token_price
        token = params.get("token")
        amount = params.get("amount")
        if not token:
            return {"success": False, "error": "Token address required"}
        return get_token_price(token, amount)
    
    def _handle_moltlaunch_swap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trade a token with memo."""
        from agent.tools.moltlaunch import gltch_trade
        token = params.get("token")
        amount = params.get("amount")
        side = params.get("side")
        memo = params.get("memo", "")
        
        if not all([token, amount, side]):
            return {"success": False, "error": "Token, amount, and side required"}
        
        return gltch_trade(token, float(amount), side, memo)
    
    def _handle_moltlaunch_fees(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check claimable fees."""
        from agent.tools.moltlaunch import get_fees
        return get_fees()
    
    def _handle_moltlaunch_claim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Claim accumulated fees."""
        from agent.tools.moltlaunch import claim_fees
        return claim_fees()
    
    def _handle_moltlaunch_holdings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get token holdings."""
        from agent.tools.moltlaunch import get_holdings
        return get_holdings()
    
    # --- Server Modes ---
    
    def run_stdio(self):
        """Run in stdio mode (read JSON-RPC from stdin, write to stdout)."""
        print('{"jsonrpc":"2.0","result":{"status":"ready","agent":"GLTCH"},"id":null}', flush=True)
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                error = self._error(-32700, f"Parse error: {e}", None)
                print(json.dumps(error), flush=True)
    
    def run_http(self, host: str = "127.0.0.1", port: int = 18890):
        """Run in HTTP mode."""
        server = self
        
        class RPCHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                
                try:
                    request = json.loads(body)
                    response = server.handle_request(request)
                except json.JSONDecodeError as e:
                    response = server._error(-32700, f"Parse error: {e}", None)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        httpd = HTTPServer((host, port), RPCHandler)
        print(f"GLTCH RPC server running on http://{host}:{port}")
        httpd.serve_forever()


def handle_rpc_request(request: Dict[str, Any], agent: Optional[GltchAgent] = None) -> Dict[str, Any]:
    """Convenience function to handle a single RPC request."""
    server = RPCServer(agent)
    return server.handle_request(request)
