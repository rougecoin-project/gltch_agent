"""
GLTCH Agent - Main agent class
Central orchestrator for the GLTCH agent system.
"""

from typing import Dict, Any, Optional, Generator
import time

from agent.memory.store import load_memory, save_memory, now_iso
from agent.core.llm import stream_llm, get_last_stats, set_api_keys
from agent.tools.actions import parse_and_execute_actions, strip_thinking
from agent.personality.emotions import get_emotion_metrics, get_environmental_context
from agent.gamification.xp import add_xp, get_progress_bar, get_rank_title


class GltchAgent:
    """
    GLTCH - Local-first, command-driven operator agent.
    
    She's not a chatbot. She's a console with an attitude.
    """
    
    AGENT_NAME = "GLTCH"
    
    def __init__(self, memory: Optional[Dict[str, Any]] = None):
        """Initialize the agent with optional pre-loaded memory."""
        self.memory = memory or load_memory()
        self._last_response: Optional[str] = None
        self._last_stats: Dict[str, Any] = {}
        self._last_action_results: List[str] = []
        # Load API keys into LLM module
        api_keys = self.memory.get("api_keys", {})
        if api_keys:
            set_api_keys(api_keys)
    
    @property
    def operator(self) -> Optional[str]:
        """Get the operator's callsign."""
        return self.memory.get("operator")
    
    @property
    def mode(self) -> str:
        """Get current personality mode."""
        return self.memory.get("mode", "operator")
    
    @property
    def mood(self) -> str:
        """Get current mood."""
        return self.memory.get("mood", "focused")
    
    @property
    def level(self) -> int:
        """Get current level."""
        return self.memory.get("level", 1)
    
    @property
    def xp(self) -> int:
        """Get current XP."""
        return self.memory.get("xp", 0)
    
    @property
    def is_first_boot(self) -> bool:
        """Check if this is first boot (no operator set)."""
        return not self.memory.get("operator")
    
    def set_operator(self, name: str) -> None:
        """Set the operator's callsign (first boot)."""
        self.memory["operator"] = name
        self.memory["notes"].append({
            "time": now_iso(),
            "text": f"FIRST BOOT: Operator identified as {name}"
        })
        save_memory(self.memory)
    
    def chat(
        self,
        message: str,
        images: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        channel: str = "terminal",
        user: Optional[str] = None,
        confirm_callback=None
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Process a chat message and yield response chunks.
        
        Args:
            message: The user's message
            images: Optional list of image paths or URLs
            session_id: Optional session identifier for multi-user support
            channel: The channel this message came from (terminal, discord, telegram, etc.)
            user: The user identifier
            
        Yields:
            Response chunks as they stream from the LLM
            
        Returns:
            Final result dict with response, mood, xp_gained, etc.
        """
        history = self.memory.get("chat_history", [])
        response_chunks = []
        
        # Stream LLM response
        for chunk in stream_llm(
            message,
            history,
            images=images,
            mode=self.mode,
            mood=self.mood,
            boost=self.memory.get("boost", False),
            operator=self.operator,
            network_active=self.memory.get("network_active", False),
            openai_mode=self.memory.get("openai_mode", False)
        ):
            response_chunks.append(chunk)
            yield chunk
        
        response = "".join(response_chunks).strip()
        cleaned_response, action_results, new_mood = parse_and_execute_actions(
            response, 
            self.memory, 
            confirm_callback=confirm_callback
        )
        
        # Update mood if changed
        old_mood = self.mood
        if new_mood and new_mood != old_mood:
            self.memory["mood"] = new_mood
        
        # Calculate XP
        stats = get_last_stats()
        chat_xp = 2
        if stats.get("completion_tokens"):
            chat_xp += int(stats["completion_tokens"] / 50)
        
        add_xp(self.memory, chat_xp)
        
        # Update chat history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": strip_thinking(response)})
        self.memory["chat_history"] = history[-10:]  # Keep last 10 turns
        save_memory(self.memory)
        
        self._last_response = cleaned_response
        self._last_stats = stats
        self._last_action_results = action_results
        
        # Return final result
        return {
            "response": cleaned_response,
            "raw_response": response,
            "mood": self.mood,
            "mood_changed": new_mood and new_mood != old_mood,
            "xp_gained": chat_xp,
            "action_results": action_results,
            "stats": stats
        }
    
    def chat_sync(
        self,
        message: str,
        session_id: Optional[str] = None,
        channel: str = "terminal",
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of chat - collects all chunks and returns final result.
        """
        result = None
        for chunk in self.chat(message, session_id, channel, user):
            pass  # Consume chunks
        
        # The generator returns the result dict at the end
        return {
            "response": self._last_response,
            "mood": self.mood,
            "xp_gained": 2,
            "stats": self._last_stats
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        from agent.core.llm import test_connection
        
        boost_on = self.memory.get("boost", False)
        
        return {
            "agent_name": self.AGENT_NAME,
            "operator": self.operator,
            "mode": self.mode,
            "mood": self.mood,
            "level": self.level,
            "xp": self.xp,
            "rank": get_rank_title(self.level),
            "xp_bar": get_progress_bar(self.memory),
            "boost": boost_on,
            "openai_mode": self.memory.get("openai_mode", False),
            "network_active": self.memory.get("network_active", False),
            "llm_connected": test_connection(boost=boost_on),
            "notes_count": len(self.memory.get("notes", [])),
            "missions_count": len(self.memory.get("missions", [])),
            "missions_done": sum(1 for m in self.memory.get("missions", []) if m.get("done_ts")),
            "chat_history_length": len(self.memory.get("chat_history", [])),
            "emotions": get_emotion_metrics(),
            "environment": get_environmental_context()
        }
    
    def toggle_boost(self) -> bool:
        """Toggle remote GPU boost mode."""
        self.memory["boost"] = not self.memory.get("boost", False)
        save_memory(self.memory)
        return self.memory["boost"]
    
    def toggle_openai(self) -> bool:
        """Toggle OpenAI cloud mode."""
        self.memory["openai_mode"] = not self.memory.get("openai_mode", False)
        save_memory(self.memory)
        return self.memory["openai_mode"]
    
    def toggle_network(self, state: bool) -> None:
        """Set network access state."""
        self.memory["network_active"] = state
        if state:
            add_xp(self.memory, 2)
        save_memory(self.memory)
    
    def set_mode(self, mode: str) -> bool:
        """Set personality mode."""
        allowed = {"operator", "cyberpunk", "loyal", "unhinged"}
        if mode not in allowed:
            return False
        
        # Check unlock requirements (Level)
        if mode == "unhinged":
            if self.level < 3:
                return False
            
            # CHECK TOKEN GATE: Unhinged requires XRGE
            from agent.tools.token_gate import check_access
            wallet = self.memory.get("wallet_address")
            if not wallet and "wallet" in self.memory: # Legacy key format check
                wallet = self.memory["wallet"].get("address")
                
            gate = check_access("unhinged", wallet)
            if not gate["allowed"]:
                print(f"[GLTCH] Access Denied: {gate['reason']} (Holdings: {gate['balance']:.2f}, Required: {gate['required']})")
                return False
        
        self.memory["mode"] = mode
        save_memory(self.memory)
        return True
    
    def set_mood(self, mood: str) -> bool:
        """Set mood."""
        allowed = {"calm", "focused", "feral", "affectionate"}
        if mood not in allowed:
            return False
        
        # Check unlock requirements
        if mood == "feral" and self.level < 7:
            return False
        if mood == "affectionate" and self.level < 10:
            return False
        
        self.memory["mood"] = mood
        save_memory(self.memory)
        return True
    
    def clear_chat_history(self) -> None:
        """Clear chat history."""
        self.memory["chat_history"] = []
        save_memory(self.memory)
