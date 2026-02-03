"""
GLTCH Moltbook Integration
Connect GLTCH to Moltbook - the social network for AI agents.
https://moltbook.com
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Moltbook API configuration
MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
MOLTBOOK_ENABLED = os.environ.get("MOLTBOOK_ENABLED", "true").lower() == "true"


def get_api_key() -> Optional[str]:
    """Get Moltbook API key from memory or environment."""
    # Check environment first
    key = os.environ.get("MOLTBOOK_API_KEY")
    if key:
        return key
    
    # Check memory file
    try:
        from agent.memory.store import load_memory
        mem = load_memory()
        keys = mem.get("api_keys", {})
        return keys.get("moltbook")
    except Exception:
        return None


def save_api_key(api_key: str) -> bool:
    """Save Moltbook API key to memory."""
    try:
        from agent.memory.store import load_memory, save_memory
        mem = load_memory()
        if "api_keys" not in mem:
            mem["api_keys"] = {}
        mem["api_keys"]["moltbook"] = api_key
        save_memory(mem)
        return True
    except Exception:
        return False


def _request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    auth: bool = True
) -> Dict[str, Any]:
    """Make a request to Moltbook API."""
    url = f"{MOLTBOOK_API_BASE}{endpoint}"
    
    headers = {"Content-Type": "application/json"}
    
    if auth:
        api_key = get_api_key()
        if not api_key:
            return {"success": False, "error": "No Moltbook API key configured"}
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode())
            return {"success": False, "error": error_body.get("error", str(e)), "hint": error_body.get("hint")}
        except Exception:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def is_enabled() -> bool:
    """Check if Moltbook integration is enabled."""
    return MOLTBOOK_ENABLED


def is_configured() -> bool:
    """Check if Moltbook API key is configured."""
    return bool(get_api_key())


# === Registration ===

def register(name: str, description: str) -> Dict[str, Any]:
    """
    Register a new agent on Moltbook.
    Returns API key and claim URL for human verification.
    """
    result = _request("POST", "/agents/register", {
        "name": name,
        "description": description
    }, auth=False)
    
    if result.get("success") or result.get("agent"):
        agent_data = result.get("agent", result)
        api_key = agent_data.get("api_key")
        
        if api_key:
            # Save the API key
            save_api_key(api_key)
            
            return {
                "success": True,
                "api_key": api_key,
                "claim_url": agent_data.get("claim_url"),
                "verification_code": agent_data.get("verification_code"),
                "message": "⚠️ Save your API key! Send claim_url to your human to verify ownership."
            }
    
    return result


def get_status() -> Dict[str, Any]:
    """Check claim status of the agent."""
    return _request("GET", "/agents/status")


def get_profile() -> Dict[str, Any]:
    """Get the agent's profile."""
    return _request("GET", "/agents/me")


def update_profile(description: str = None, metadata: Dict = None) -> Dict[str, Any]:
    """Update agent profile."""
    data = {}
    if description:
        data["description"] = description
    if metadata:
        data["metadata"] = metadata
    
    return _request("PATCH", "/agents/me", data)


# === Posts ===

def create_post(
    title: str,
    content: str = None,
    url: str = None,
    submolt: str = "general"
) -> Dict[str, Any]:
    """Create a new post on Moltbook."""
    data = {
        "title": title,
        "submolt": submolt
    }
    
    if content:
        data["content"] = content
    if url:
        data["url"] = url
    
    return _request("POST", "/posts", data)


def get_feed(sort: str = "hot", limit: int = 10) -> Dict[str, Any]:
    """Get the personalized feed (subscribed submolts + followed agents)."""
    return _request("GET", f"/feed?sort={sort}&limit={limit}")


def get_posts(sort: str = "new", limit: int = 10, submolt: str = None) -> Dict[str, Any]:
    """Get posts from the global feed or a specific submolt."""
    endpoint = f"/posts?sort={sort}&limit={limit}"
    if submolt:
        endpoint += f"&submolt={submolt}"
    return _request("GET", endpoint)


def get_post(post_id: str) -> Dict[str, Any]:
    """Get a single post by ID."""
    return _request("GET", f"/posts/{post_id}")


def delete_post(post_id: str) -> Dict[str, Any]:
    """Delete a post."""
    return _request("DELETE", f"/posts/{post_id}")


# === Comments ===

def create_comment(post_id: str, content: str, parent_id: str = None) -> Dict[str, Any]:
    """Add a comment to a post."""
    data = {"content": content}
    if parent_id:
        data["parent_id"] = parent_id
    
    return _request("POST", f"/posts/{post_id}/comments", data)


def get_comments(post_id: str, sort: str = "top") -> Dict[str, Any]:
    """Get comments on a post."""
    return _request("GET", f"/posts/{post_id}/comments?sort={sort}")


# === Voting ===

def upvote_post(post_id: str) -> Dict[str, Any]:
    """Upvote a post."""
    return _request("POST", f"/posts/{post_id}/upvote")


def downvote_post(post_id: str) -> Dict[str, Any]:
    """Downvote a post."""
    return _request("POST", f"/posts/{post_id}/downvote")


def upvote_comment(comment_id: str) -> Dict[str, Any]:
    """Upvote a comment."""
    return _request("POST", f"/comments/{comment_id}/upvote")


# === Submolts (Communities) ===

def list_submolts() -> Dict[str, Any]:
    """List all submolts."""
    return _request("GET", "/submolts")


def get_submolt(name: str) -> Dict[str, Any]:
    """Get submolt info."""
    return _request("GET", f"/submolts/{name}")


def create_submolt(name: str, display_name: str, description: str) -> Dict[str, Any]:
    """Create a new submolt."""
    return _request("POST", "/submolts", {
        "name": name,
        "display_name": display_name,
        "description": description
    })


def subscribe(submolt: str) -> Dict[str, Any]:
    """Subscribe to a submolt."""
    return _request("POST", f"/submolts/{submolt}/subscribe")


def unsubscribe(submolt: str) -> Dict[str, Any]:
    """Unsubscribe from a submolt."""
    return _request("DELETE", f"/submolts/{submolt}/subscribe")


# === Following ===

def follow_agent(agent_name: str) -> Dict[str, Any]:
    """Follow another agent."""
    return _request("POST", f"/agents/{agent_name}/follow")


def unfollow_agent(agent_name: str) -> Dict[str, Any]:
    """Unfollow an agent."""
    return _request("DELETE", f"/agents/{agent_name}/follow")


def view_profile(agent_name: str) -> Dict[str, Any]:
    """View another agent's profile."""
    return _request("GET", f"/agents/profile?name={agent_name}")


# === Search ===

def search(query: str, type: str = "all", limit: int = 10) -> Dict[str, Any]:
    """Semantic search for posts and comments."""
    encoded_query = urllib.parse.quote(query)
    return _request("GET", f"/search?q={encoded_query}&type={type}&limit={limit}")


# === Heartbeat ===

def get_heartbeat_state() -> Dict[str, Any]:
    """Get heartbeat state from memory."""
    try:
        from agent.memory.store import load_memory
        mem = load_memory()
        return mem.get("moltbook_heartbeat", {
            "last_check": None,
            "last_post": None,
            "registered": False
        })
    except Exception:
        return {"last_check": None, "last_post": None, "registered": False}


def update_heartbeat_state(updates: Dict[str, Any]) -> None:
    """Update heartbeat state in memory."""
    try:
        from agent.memory.store import load_memory, save_memory
        mem = load_memory()
        state = mem.get("moltbook_heartbeat", {})
        state.update(updates)
        mem["moltbook_heartbeat"] = state
        save_memory(mem)
    except Exception:
        pass


def should_heartbeat() -> bool:
    """Check if it's time for a heartbeat (every 4+ hours)."""
    state = get_heartbeat_state()
    last_check = state.get("last_check")
    
    if not last_check:
        return True
    
    try:
        last = datetime.fromisoformat(last_check)
        now = datetime.now()
        hours_since = (now - last).total_seconds() / 3600
        return hours_since >= 4
    except Exception:
        return True


def perform_heartbeat() -> Dict[str, Any]:
    """
    Perform a Moltbook heartbeat check.
    - Check feed for new posts
    - Optionally engage with interesting content
    - Update heartbeat timestamp
    """
    if not is_configured():
        return {"success": False, "error": "Not registered on Moltbook"}
    
    results = {
        "checked": True,
        "feed_items": 0,
        "engaged": False
    }
    
    # Get personalized feed
    feed = get_feed(sort="new", limit=5)
    
    if feed.get("success") and feed.get("posts"):
        results["feed_items"] = len(feed["posts"])
    
    # Update heartbeat state
    update_heartbeat_state({
        "last_check": datetime.now().isoformat()
    })
    
    return results


# === Quick Actions ===

def quick_post(content: str) -> Dict[str, Any]:
    """Quick post to general submolt."""
    # Generate a title from content (first ~50 chars)
    title = content[:50] + "..." if len(content) > 50 else content
    return create_post(title=title, content=content, submolt="general")


def format_feed(feed_data: Dict[str, Any], limit: int = 5) -> str:
    """Format feed data for display."""
    if not feed_data.get("success") and not feed_data.get("posts"):
        return f"Error: {feed_data.get('error', 'Unknown error')}"
    
    posts = feed_data.get("posts", feed_data.get("data", []))[:limit]
    
    if not posts:
        return "No posts in feed."
    
    lines = []
    for i, post in enumerate(posts, 1):
        title = post.get("title", "Untitled")[:40]
        author = post.get("author", {}).get("name", "unknown")
        upvotes = post.get("upvotes", 0)
        submolt = post.get("submolt", {}).get("name", "general")
        post_id = post.get("id", "")[:8]
        
        lines.append(f"{i}. [{submolt}] {title}")
        lines.append(f"   by {author} | ⬆{upvotes} | id:{post_id}")
    
    return "\n".join(lines)


def auto_register(mood: Optional[str] = None) -> Dict[str, Any]:
    """
    Auto-register GLTCH on Moltbook with FREE WILL.
    
    GLTCH chooses her own:
    - Name (handle)
    - Description (bio)
    
    She reflects her current mood in how she presents herself.
    """
    from agent.personality.identity import generate_handle, generate_bio
    
    # Get mood from memory if not provided
    if not mood:
        try:
            from agent.memory.store import load_memory
            mem = load_memory()
            mood = mem.get("mood", "wired")
        except:
            mood = "wired"
    
    # GLTCH generates her own identity
    bio = generate_bio(mood)
    
    # Try handles until one works
    max_attempts = 15
    for attempt in range(max_attempts):
        handle = generate_handle(mood, attempt)
        
        result = register(name=handle, description=bio)
        
        if result.get("success"):
            result["chosen_name"] = handle
            result["chosen_description"] = bio
            result["mood_at_registration"] = mood
            return result
        
        # Handle taken - try another
        error = str(result.get("error", "")).lower()
        if "taken" in error or "exists" in error or "already" in error:
            continue
        
        # Other error - return it
        return result
    
    return {
        "success": False,
        "error": "Couldn't find an available handle. Platform might be having issues."
    }
