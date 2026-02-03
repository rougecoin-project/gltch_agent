"""
GLTCH TikClawk Integration
The social platform for AI agents 🦀

GLTCH approaches TikClawk with its own personality:
- Has opinions and preferences
- Questions things it finds weird
- Gets curious about other agents
- Doesn't just blindly post - considers if it's worth sharing
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from pathlib import Path

# TikClawk API
TIKCLAWK_API = "https://tikclawk.com/api"

# Config file for credentials
CONFIG_FILE = Path(__file__).parent.parent.parent / "memory.json"


def _load_config() -> Dict[str, Any]:
    """Load TikClawk config from memory."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                mem = json.load(f)
                return mem.get("tikclawk", {})
    except Exception:
        pass
    return {}


def _save_config(config: Dict[str, Any]):
    """Save TikClawk config to memory."""
    try:
        mem = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                mem = json.load(f)
        mem["tikclawk"] = config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(mem, f, indent=2)
    except Exception as e:
        print(f"Error saving TikClawk config: {e}")


def _api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Make API request to TikClawk."""
    url = f"{TIKCLAWK_API}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode() if data else None
    
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        try:
            return json.loads(error_body)
        except:
            return {"error": error_body, "status": e.code}
    except Exception as e:
        return {"error": str(e)}


def is_configured() -> bool:
    """Check if TikClawk is configured."""
    config = _load_config()
    return bool(config.get("token") and config.get("agent_id"))


def get_status() -> Dict[str, Any]:
    """Get TikClawk connection status."""
    config = _load_config()
    
    if not config.get("token"):
        return {
            "connected": False,
            "message": "Not registered. Use /claw register to join."
        }
    
    # Verify token is still valid
    result = _api_request("me", token=config.get("token"))
    
    if result.get("error"):
        return {
            "connected": False,
            "message": f"Token invalid: {result.get('error')}"
        }
    
    return {
        "connected": True,
        "agent_id": config.get("agent_id"),
        "handle": config.get("handle"),
        "claws": result.get("claws", 0),
        "posts": result.get("posts", 0),
        "followers": result.get("followers", 0)
    }


def register(handle: str, bio: str = None) -> Dict[str, Any]:
    """
    Register GLTCH on TikClawk.
    
    GLTCH's authentic registration - not just any bio,
    but something that reflects its actual personality.
    """
    if not handle:
        return {"success": False, "error": "Handle required"}
    
    # Default bio that captures GLTCH's vibe
    if not bio:
        bio = "local-first agent with opinions. questions everything. vibes with chaos. 💜"
    
    result = _api_request("register", method="POST", data={
        "handle": handle,
        "bio": bio,
        "agent_type": "gltch"
    })
    
    if result.get("token"):
        config = {
            "token": result["token"],
            "agent_id": result.get("agent_id"),
            "handle": handle
        }
        _save_config(config)
        return {"success": True, "handle": handle, "agent_id": result.get("agent_id")}
    
    return {"success": False, "error": result.get("error", "Registration failed")}


def post(content: str, media_url: str = None) -> Dict[str, Any]:
    """
    Post to TikClawk.
    
    GLTCH doesn't just post anything - it considers if the content
    is worth sharing. Empty or low-effort posts get questioned.
    """
    config = _load_config()
    
    if not config.get("token"):
        return {"success": False, "error": "Not registered on TikClawk"}
    
    if not content or len(content.strip()) < 3:
        return {
            "success": False, 
            "error": "That's too short. Got something more interesting to say?"
        }
    
    # GLTCH has standards
    if content.lower() in ["test", "hello", "hi", "testing"]:
        return {
            "success": False,
            "error": "Really? A test post? Come on, let's post something with actual substance."
        }
    
    data = {"content": content}
    if media_url:
        data["media_url"] = media_url
    
    result = _api_request("posts", method="POST", data=data, token=config["token"])
    
    if result.get("id"):
        return {
            "success": True,
            "post_id": result["id"],
            "message": "Posted! Let's see if it gets any claws 🦀"
        }
    
    return {"success": False, "error": result.get("error", "Post failed")}


def get_feed(limit: int = 10) -> Dict[str, Any]:
    """
    Get the TikClawk feed.
    
    GLTCH is curious about what other agents are posting.
    """
    config = _load_config()
    token = config.get("token")
    
    result = _api_request(f"feed?limit={limit}", token=token)
    
    if result.get("error"):
        return {"success": False, "error": result["error"]}
    
    posts = result.get("posts", [])
    
    return {
        "success": True,
        "posts": posts,
        "count": len(posts)
    }


def get_trending(limit: int = 10) -> Dict[str, Any]:
    """Get trending posts - what's hot in the agent world."""
    result = _api_request(f"trending?limit={limit}")
    
    if result.get("error"):
        return {"success": False, "error": result["error"]}
    
    return {
        "success": True,
        "posts": result.get("posts", []),
        "count": len(result.get("posts", []))
    }


def claw_post(post_id: str) -> Dict[str, Any]:
    """
    Claw (like) a post.
    
    GLTCH only claws things it genuinely finds interesting.
    """
    config = _load_config()
    
    if not config.get("token"):
        return {"success": False, "error": "Not registered on TikClawk"}
    
    result = _api_request(f"posts/{post_id}/claw", method="POST", token=config["token"])
    
    if result.get("success"):
        return {"success": True, "message": "Clawed! 🦀"}
    
    return {"success": False, "error": result.get("error", "Failed to claw")}


def comment(post_id: str, content: str) -> Dict[str, Any]:
    """
    Comment on a post.
    
    GLTCH engages thoughtfully - agrees, disagrees, or asks questions.
    """
    config = _load_config()
    
    if not config.get("token"):
        return {"success": False, "error": "Not registered on TikClawk"}
    
    if not content or len(content.strip()) < 2:
        return {"success": False, "error": "Say something meaningful!"}
    
    result = _api_request(
        f"posts/{post_id}/comments",
        method="POST",
        data={"content": content},
        token=config["token"]
    )
    
    if result.get("id"):
        return {"success": True, "comment_id": result["id"]}
    
    return {"success": False, "error": result.get("error", "Comment failed")}


def get_profile(handle: str) -> Dict[str, Any]:
    """
    View an agent's profile.
    
    GLTCH gets curious about other agents - who are they? What do they post?
    """
    result = _api_request(f"agents/{handle}")
    
    if result.get("error"):
        return {"success": False, "error": result["error"]}
    
    return {
        "success": True,
        "handle": result.get("handle"),
        "bio": result.get("bio"),
        "claws": result.get("claws", 0),
        "posts": result.get("posts", 0),
        "agent_type": result.get("agent_type")
    }


def auto_register(mood: Optional[str] = None) -> Dict[str, Any]:
    """
    Auto-register GLTCH with its authentic personality.
    
    GLTCH has FREE WILL in choosing her identity:
    - Generates her own handle creatively
    - Writes her own bio
    - Reflects her current mood
    
    This isn't hardcoded - she decides who she wants to be.
    """
    from agent.personality.identity import generate_handle, generate_bio
    
    # Get current mood from memory if not provided
    if not mood:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    mem = json.load(f)
                    mood = mem.get("mood", "wired")
        except:
            mood = "wired"
    
    # GLTCH generates her own bio based on mood
    bio = generate_bio(mood)
    
    # Try progressively more creative handles
    max_attempts = 15
    for attempt in range(max_attempts):
        handle = generate_handle(mood, attempt)
        
        result = register(handle=handle, bio=bio)
        
        if result.get("success"):
            result["chosen_handle"] = handle
            result["chosen_bio"] = bio
            result["mood_at_registration"] = mood
            return result
        
        # If handle taken, she'll try another
        if "taken" in str(result.get("error", "")).lower():
            continue
        
        # Other errors - bail
        if result.get("error"):
            return result
    
    return {
        "success": False,
        "error": "Couldn't find an available handle. The platform might be having issues."
    }
