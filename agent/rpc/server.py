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
            "get_sessions": self._handle_get_sessions,
            "clear_session": self._handle_clear_session,
            "ping": self._handle_ping
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
