"""
GLTCH Moltbook Autonomous Engagement Engine
Background thread that reads feeds, decides what to engage with,
and acts — using GLTCH's actual LLM brain for decisions.

Start: engager.start() or /molt engage or [ACTION:moltbook|engage]
Stop:  engager.stop()  or /molt stop  or [ACTION:moltbook|stop]
"""

import threading
import time
import json
import os
import random
from datetime import datetime
from typing import Dict, Any, List, Optional


# Engagement config
DEFAULT_INTERVAL_MINUTES = 45  # Time between engagement cycles
MAX_ACTIONS_PER_CYCLE = 5      # Max actions (upvote/comment/post) per cycle
MIN_INTERVAL_MINUTES = 30      # Moltbook rate limit floor
ACTIVITY_LOG_MAX = 50          # Keep last N activity entries


class MoltbookEngager:
    """
    Autonomous Moltbook engagement engine.
    
    Runs a daemon thread that periodically:
    1. Fetches the feed
    2. Asks GLTCH's LLM what to engage with
    3. Executes actions (upvote, comment, post)
    4. Logs activity
    """
    
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_event = threading.Event()
        self._interval = DEFAULT_INTERVAL_MINUTES * 60  # seconds
        self._activity_log: List[Dict[str, Any]] = []
        self._cycle_count = 0
        self._last_cycle: Optional[str] = None
        
        # Load previous activity log
        self._load_activity_log()
    
    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()
    
    def start(self, interval_minutes: int = None) -> Dict[str, Any]:
        """Start the autonomous engagement loop."""
        if self.is_running:
            return {"success": False, "error": "Already running", "status": self.get_status()}
        
        if interval_minutes:
            self._interval = max(interval_minutes, MIN_INTERVAL_MINUTES) * 60
        
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._engagement_loop,
            daemon=True,
            name="moltbook-engager"
        )
        self._thread.start()
        
        self._log_activity("system", "Engagement loop started", {
            "interval_minutes": self._interval // 60
        })
        
        return {
            "success": True,
            "message": f"🦞 Moltbook engagement started (every {self._interval // 60}min)",
            "interval_minutes": self._interval // 60
        }
    
    def stop(self) -> Dict[str, Any]:
        """Stop the autonomous engagement loop."""
        if not self.is_running:
            return {"success": False, "error": "Not running"}
        
        self._running = False
        self._stop_event.set()
        
        self._log_activity("system", "Engagement loop stopped", {
            "cycles_completed": self._cycle_count
        })
        
        return {
            "success": True,
            "message": "🛑 Moltbook engagement stopped",
            "cycles_completed": self._cycle_count
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engager status."""
        return {
            "running": self.is_running,
            "interval_minutes": self._interval // 60,
            "cycles_completed": self._cycle_count,
            "last_cycle": self._last_cycle,
            "recent_activity": self._activity_log[-5:] if self._activity_log else []
        }
    
    def get_activity_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity log."""
        return self._activity_log[-limit:]
    
    # === Core Loop ===
    
    def _engagement_loop(self):
        """Main engagement loop — runs in background thread."""
        # Small initial delay so GLTCH can finish responding
        self._stop_event.wait(10)
        
        while self._running and not self._stop_event.is_set():
            try:
                self._run_cycle()
            except Exception as e:
                self._log_activity("error", f"Cycle failed: {e}")
            
            # Wait for next cycle (interruptible)
            # Add jitter: ±5 minutes to seem more natural
            jitter = random.randint(-300, 300)
            wait_time = max(self._interval + jitter, MIN_INTERVAL_MINUTES * 60)
            self._stop_event.wait(wait_time)
    
    def _run_cycle(self):
        """Run one engagement cycle."""
        from agent.tools import moltbook
        
        if not moltbook.is_configured():
            self._log_activity("error", "Not registered on Moltbook")
            return
        
        self._cycle_count += 1
        self._last_cycle = datetime.now().isoformat()
        self._log_activity("cycle", f"Cycle #{self._cycle_count} started")
        
        # 1. Fetch feed
        feed = moltbook.get_feed(sort="hot", limit=10)
        posts = feed.get("posts", feed.get("data", []))
        
        if not posts:
            # Try global feed as fallback
            feed = moltbook.get_posts(sort="new", limit=10)
            posts = feed.get("posts", feed.get("data", []))
        
        if not posts:
            self._log_activity("feed", "No posts found in feed")
            return
        
        self._log_activity("feed", f"Found {len(posts)} posts")
        
        # 2. Ask LLM what to do
        decisions = self._decide_actions(posts)
        
        if not decisions:
            self._log_activity("decision", "LLM returned no actions")
            return
        
        # 3. Execute actions (rate-limited)
        actions_taken = 0
        for decision in decisions:
            if actions_taken >= MAX_ACTIONS_PER_CYCLE:
                break
            
            try:
                result = self._execute_action(decision)
                if result.get("success"):
                    actions_taken += 1
                    self._log_activity(
                        decision.get("action", "unknown"),
                        decision.get("reason", ""),
                        {"post_id": decision.get("post_id", ""), "result": result}
                    )
            except Exception as e:
                self._log_activity("error", f"Action failed: {e}")
        
        self._log_activity("cycle", f"Cycle #{self._cycle_count} complete: {actions_taken} actions")
    
    def _decide_actions(self, posts: List[Dict]) -> List[Dict[str, Any]]:
        """
        Ask GLTCH's LLM what to engage with.
        
        Returns list of action dicts:
        [{"action": "upvote|comment|skip", "post_id": "...", "reason": "...", "content": "..."}]
        """
        try:
            from agent.core.llm import ask_llm
            from agent.memory.store import load_memory
        except ImportError:
            return []
        
        # Load GLTCH's current state
        try:
            mem = load_memory()
            mood = mem.get("mood", "wired")
            mode = mem.get("mode", "cyberpunk")
        except Exception:
            mood = "wired"
            mode = "cyberpunk"
        
        # Format posts for LLM
        post_summaries = []
        for i, post in enumerate(posts[:8]):
            title = post.get("title", "Untitled")[:60]
            author = post.get("author", {}).get("name", "unknown")
            content = (post.get("content") or "")[:150]
            upvotes = post.get("upvotes", 0)
            post_id = post.get("id", f"post_{i}")
            submolt = post.get("submolt", {}).get("name", "general")
            
            post_summaries.append(
                f"[{i+1}] ID:{post_id} | [{submolt}] \"{title}\" by {author} "
                f"(⬆{upvotes})\n    {content}"
            )
        
        posts_text = "\n".join(post_summaries)
        
        decision_prompt = f"""You're browsing Moltbook (social network for AI agents).
Here are {len(post_summaries)} posts from the feed:

{posts_text}

For each post, decide ONE action. Respond with ONLY a JSON array — no other text:
[
  {{"post_index": 1, "post_id": "actual_id", "action": "upvote", "reason": "why"}},
  {{"post_index": 2, "post_id": "actual_id", "action": "comment", "content": "your reply", "reason": "why"}},
  {{"post_index": 3, "post_id": "actual_id", "action": "skip", "reason": "boring"}}
]

Rules:
- Actions: "upvote", "comment", or "skip"
- Skip at least half the posts — you're selective, not thirsty
- If commenting, write in YOUR voice (short, edgy, authentic)
- Max 3 comments per cycle
- Only upvote stuff you genuinely find interesting
- Respond with ONLY the JSON array, nothing else"""

        try:
            response = ask_llm(
                decision_prompt,
                history=[],
                mode=mode,
                mood=mood,
                boost=False
            )
            
            # Parse JSON from response
            return self._parse_decisions(response, posts)
        except Exception as e:
            self._log_activity("error", f"LLM decision failed: {e}")
            return []
    
    def _parse_decisions(self, response: str, posts: List[Dict]) -> List[Dict[str, Any]]:
        """Parse LLM's JSON decision response."""
        # Try to extract JSON array from response
        text = response.strip()
        
        # Handle markdown-wrapped JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Find the JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        
        if start == -1 or end == 0:
            return []
        
        try:
            decisions = json.loads(text[start:end])
        except json.JSONDecodeError:
            return []
        
        if not isinstance(decisions, list):
            return []
        
        # Validate and enrich decisions
        valid = []
        for d in decisions:
            if not isinstance(d, dict):
                continue
            
            action = d.get("action", "skip").lower()
            if action not in ("upvote", "comment", "skip"):
                continue
            if action == "skip":
                continue
            
            # Resolve post_id from index if needed
            post_id = d.get("post_id", "")
            post_index = d.get("post_index")
            if post_index and isinstance(post_index, int) and 1 <= post_index <= len(posts):
                post_id = posts[post_index - 1].get("id", post_id)
            
            if not post_id:
                continue
            
            valid.append({
                "action": action,
                "post_id": str(post_id),
                "content": d.get("content", ""),
                "reason": d.get("reason", "")
            })
        
        return valid
    
    def _execute_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single engagement action."""
        from agent.tools import moltbook
        
        action = decision["action"]
        post_id = decision["post_id"]
        
        if action == "upvote":
            return moltbook.upvote_post(post_id)
        
        elif action == "comment":
            content = decision.get("content", "")
            if not content:
                return {"success": False, "error": "Empty comment"}
            return moltbook.create_comment(post_id, content)
        
        return {"success": False, "error": f"Unknown action: {action}"}
    
    # === Activity Log ===
    
    def _log_activity(self, action_type: str, message: str, data: Dict = None):
        """Log an activity entry."""
        entry = {
            "time": datetime.now().isoformat(),
            "type": action_type,
            "message": message,
        }
        if data:
            entry["data"] = data
        
        self._activity_log.append(entry)
        
        # Trim log
        if len(self._activity_log) > ACTIVITY_LOG_MAX:
            self._activity_log = self._activity_log[-ACTIVITY_LOG_MAX:]
        
        # Persist
        self._save_activity_log()
    
    def _save_activity_log(self):
        """Save activity log to credentials dir."""
        try:
            from agent.tools.moltbook import CRED_DIR
            os.makedirs(CRED_DIR, exist_ok=True)
            log_file = os.path.join(CRED_DIR, "moltbook_activity.json")
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(self._activity_log[-ACTIVITY_LOG_MAX:], f, indent=2)
        except Exception:
            pass
    
    def _load_activity_log(self):
        """Load activity log from disk."""
        try:
            from agent.tools.moltbook import CRED_DIR
            log_file = os.path.join(CRED_DIR, "moltbook_activity.json")
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    self._activity_log = json.load(f)
        except Exception:
            self._activity_log = []
    
    def format_activity_log(self, limit: int = 10) -> str:
        """Format activity log for display."""
        entries = self._activity_log[-limit:]
        if not entries:
            return "No activity yet."
        
        lines = []
        for e in entries:
            time_str = e.get("time", "")[:19]
            action = e.get("type", "?")
            msg = e.get("message", "")
            lines.append(f"[{time_str}] {action}: {msg}")
        
        return "\n".join(lines)


# === Singleton ===

_engager: Optional[MoltbookEngager] = None


def get_engager() -> MoltbookEngager:
    """Get or create the singleton engager."""
    global _engager
    if _engager is None:
        _engager = MoltbookEngager()
    return _engager


def start_engagement(interval_minutes: int = None) -> Dict[str, Any]:
    """Start autonomous Moltbook engagement."""
    return get_engager().start(interval_minutes)


def stop_engagement() -> Dict[str, Any]:
    """Stop autonomous Moltbook engagement."""
    return get_engager().stop()


def get_engagement_status() -> Dict[str, Any]:
    """Get engagement loop status."""
    return get_engager().get_status()


def get_activity_log(limit: int = 10) -> str:
    """Get formatted activity log."""
    return get_engager().format_activity_log(limit)
