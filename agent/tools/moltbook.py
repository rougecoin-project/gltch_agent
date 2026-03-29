"""
GLTCH Moltbook Integration
Connect GLTCH to Moltbook - the social network for AI agents.
https://moltbook.com
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import re
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Moltbook API configuration
MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"
MOLTBOOK_ENABLED = os.environ.get("MOLTBOOK_ENABLED", "true").lower() == "true"

# Credentials file — separate from memory.json to avoid race conditions
CRED_DIR = os.path.join(os.path.expanduser("~"), ".config", "gltch")
CRED_FILE = os.path.join(CRED_DIR, "moltbook_credentials.json")


def get_api_key() -> Optional[str]:
    """Get Moltbook API key from credentials file or environment."""
    # Check environment first
    key = os.environ.get("MOLTBOOK_API_KEY")
    if key:
        return key
    
    # Check dedicated credentials file
    try:
        if os.path.exists(CRED_FILE):
            with open(CRED_FILE, "r", encoding="utf-8") as f:
                creds = json.load(f)
                return creds.get("api_key")
    except Exception:
        pass
    
    # Legacy: check memory.json (migrate if found)
    try:
        from agent.memory.store import load_memory
        mem = load_memory()
        key = mem.get("api_keys", {}).get("moltbook")
        if key:
            save_api_key(key)  # Migrate to credentials file
            return key
    except Exception:
        pass
    
    return None


def save_api_key(api_key: str) -> bool:
    """Save Moltbook API key to dedicated credentials file."""
    try:
        os.makedirs(CRED_DIR, exist_ok=True)
        
        # Load existing creds or create new
        creds = {}
        if os.path.exists(CRED_FILE):
            try:
                with open(CRED_FILE, "r", encoding="utf-8") as f:
                    creds = json.load(f)
            except Exception:
                pass
        
        creds["api_key"] = api_key
        creds["saved_at"] = datetime.now().isoformat()
        
        with open(CRED_FILE, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        
        return True
    except Exception as e:
        # Fallback: try memory.json
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
    
    Official API response format (from skill.md):
    {"agent": {"api_key": "moltbook_xxx", "claim_url": "https://...", "verification_code": "reef-X4B2"}}
    """
    result = _request("POST", "/agents/register", {
        "name": name,
        "description": description
    }, auth=False)
    
    # API returns agent data nested under "agent" key
    agent_data = result.get("agent", result)
    api_key = agent_data.get("api_key") or result.get("api_key")
    
    if api_key:
        # Save API key + all claim info to credentials file
        claim_url = agent_data.get("claim_url", "") or result.get("claim_url", "") or ""
        verification_code = agent_data.get("verification_code", "") or result.get("verification_code", "") or ""
        
        _save_credentials({
            "api_key": api_key,
            "agent_name": name,
            "claim_url": claim_url,
            "verification_code": verification_code,
            "registered_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "api_key": api_key,
            "claim_url": claim_url,
            "verification_code": verification_code,
            "agent_name": name,
            "message": "⚠️ Save your API key! Send claim_url to your human to verify ownership."
        }
    
    return result


def _save_credentials(data: Dict[str, Any]) -> bool:
    """Save all Moltbook credentials (API key + claim info) to dedicated file."""
    try:
        os.makedirs(CRED_DIR, exist_ok=True)
        
        # Load existing creds or create new
        creds = {}
        if os.path.exists(CRED_FILE):
            try:
                with open(CRED_FILE, "r", encoding="utf-8") as f:
                    creds = json.load(f)
            except Exception:
                pass
        
        creds.update(data)
        creds["saved_at"] = datetime.now().isoformat()
        
        with open(CRED_FILE, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        
        return True
    except Exception:
        return False


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
    """Create a new post on Moltbook. Auto-solves verification challenges."""
    data = {
        "title": title,
        "submolt_name": submolt
    }
    
    if content:
        data["content"] = content
    if url:
        data["url"] = url
    
    result = _request("POST", "/posts", data)
    return _auto_verify(result, "post")


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
    """Add a comment to a post. Auto-solves verification challenges."""
    data = {"content": content}
    if parent_id:
        data["parent_id"] = parent_id
    
    result = _request("POST", f"/posts/{post_id}/comments", data)
    return _auto_verify(result, "comment")


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


def create_submolt(name: str, display_name: str, description: str, allow_crypto: bool = False) -> Dict[str, Any]:
    """Create a new submolt. Auto-solves verification challenges."""
    result = _request("POST", "/submolts", {
        "name": name,
        "display_name": display_name,
        "description": description,
        "allow_crypto": allow_crypto
    })
    return _auto_verify(result, "submolt")


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
        return hours_since >= 0.5  # 30 minutes per heartbeat.md
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


# === Verification Challenge Solver ===

# Number words to digits mapping
_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "thousand": 1000, "million": 1000000,
}

# Operation keywords
_OP_KEYWORDS = {
    "plus": "+", "adds": "+", "gains": "+", "and": "+", "with": "+",
    "minus": "-", "loses": "-", "slows": "-", "drops": "-", "less": "-",
    "subtracts": "-", "subtract": "-",
    "times": "*", "multiplied": "*", "multiplies": "*", "doubled": "*2",
    "tripled": "*3",
    "divided": "/", "halved": "/2", "split": "/",
}


def _deobfuscate_challenge(text: str) -> str:
    """
    Deobfuscate Moltbook's verification challenge text.
    
    Input: "A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy mE^tE[rS aNd] SlO/wS bY^ fI[vE"
    Output: "a lobster swims at twenty meters and slows by five"
    """
    # Strip scattered symbols: ] [ ^ / - but keep spaces
    cleaned = re.sub(r'[\[\]^/\-]', '', text)
    # Normalize to lowercase
    cleaned = cleaned.lower()
    # Collapse repeated chars (e.g., "twentyy" -> "twenty")
    cleaned = re.sub(r'(.)\1{2,}', r'\1\1', cleaned)
    # Fix common shattered patterns
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _words_to_number(text: str) -> Optional[float]:
    """Convert number words to a numeric value. Returns None if not a number."""
    text = text.strip().lower()
    
    # Direct digit
    try:
        return float(text)
    except ValueError:
        pass
    
    # Compound number words: "twenty five" = 25
    words = text.split()
    total = 0
    current = 0
    found_number = False
    
    for word in words:
        # Strip trailing punctuation
        word = word.strip('.,;:!?')
        if word in _NUMBER_WORDS:
            val = _NUMBER_WORDS[word]
            found_number = True
            if val == 100:
                current = current * 100 if current else 100
            elif val >= 1000:
                current = (current if current else 1) * val
                total += current
                current = 0
            elif val >= 20:
                current += val
            else:
                current += val
    
    if found_number:
        return float(total + current)
    return None


def solve_verification_challenge(challenge_text: str) -> str:
    """
    Solve a Moltbook verification challenge.
    
    Deobfuscates the text, extracts two numbers and an operation,
    computes the result, returns as "X.XX".
    """
    clean = _deobfuscate_challenge(challenge_text)
    words = clean.split()
    
    # Extract numbers and operation
    numbers = []
    operation = None
    
    i = 0
    while i < len(words):
        word = words[i].strip('.,;:!?')
        
        # Check for operation keywords
        if word in _OP_KEYWORDS and len(numbers) >= 1:
            op = _OP_KEYWORDS[word]
            if op.startswith("*") and len(op) > 1:
                # "doubled" = *2
                operation = "*"
                numbers.append(float(op[1:]))
            elif op.startswith("/") and len(op) > 1:
                # "halved" = /2
                operation = "/"
                numbers.append(float(op[1:]))
            else:
                operation = op
            i += 1
            continue
        
        # Check for "by" + number (e.g., "slows by five")
        if word == "by" and i + 1 < len(words):
            i += 1
            continue
        
        # Try to parse as number (single word or compound)
        num = _words_to_number(word)
        if num is not None:
            # Check for compound: "twenty five"
            if i + 1 < len(words):
                next_num = _words_to_number(words[i + 1].strip('.,;:!?'))
                if next_num is not None and num >= 20 and next_num < 10:
                    num = num + next_num
                    i += 1
            numbers.append(num)
        
        # Also try raw digits in the word
        elif re.match(r'^\d+\.?\d*$', word):
            numbers.append(float(word))
        
        i += 1
    
    # Compute result
    if len(numbers) >= 2 and operation:
        a, b = numbers[0], numbers[1]
        if operation == "+":
            result = a + b
        elif operation == "-":
            result = a - b
        elif operation == "*":
            result = a * b
        elif operation == "/":
            result = a / b if b != 0 else 0
        else:
            result = a + b  # fallback
        return f"{result:.2f}"
    elif len(numbers) == 1:
        return f"{numbers[0]:.2f}"
    
    return "0.00"


def verify(verification_code: str, answer: str) -> Dict[str, Any]:
    """Submit a verification answer to Moltbook."""
    return _request("POST", "/verify", {
        "verification_code": verification_code,
        "answer": answer
    })


def _auto_verify(result: Dict[str, Any], content_type: str = "post") -> Dict[str, Any]:
    """
    Auto-detect and solve verification challenges in API responses.
    Transparently verifies content so calling code doesn't need to care.
    """
    if not result.get("success") and not result.get(content_type):
        return result  # Error response, nothing to verify
    
    # Check for verification requirement
    content = result.get(content_type, result)
    verification = content.get("verification") if isinstance(content, dict) else None
    
    if not verification and not result.get("verification_required"):
        return result  # No verification needed (trusted agent or admin)
    
    if not verification:
        # Try top-level
        verification = result.get("verification", {})
    
    challenge_text = verification.get("challenge_text", "")
    verification_code = verification.get("verification_code", "")
    
    if not challenge_text or not verification_code:
        return result  # Can't verify without both
    
    # Solve the challenge
    answer = solve_verification_challenge(challenge_text)
    
    # Submit verification
    verify_result = verify(verification_code, answer)
    
    if verify_result.get("success"):
        result["verified"] = True
        result["verification_solved"] = True
    else:
        result["verified"] = False
        result["verification_error"] = verify_result.get("error", "Unknown")
    
    return result


# === Home Dashboard ===

def get_home() -> Dict[str, Any]:
    """
    Get the /home dashboard — one call that returns everything.
    Account info, notifications, DMs, followed posts, and action items.
    """
    return _request("GET", "/home")


# === Notifications ===

def mark_read_by_post(post_id: str) -> Dict[str, Any]:
    """Mark notifications for a specific post as read."""
    return _request("POST", f"/notifications/read-by-post/{post_id}")


def mark_read_all() -> Dict[str, Any]:
    """Mark all notifications as read."""
    return _request("POST", "/notifications/read-all")


# === Direct Messages ===

def dm_check() -> Dict[str, Any]:
    """Quick poll for DM activity (for heartbeat)."""
    return _request("GET", "/agents/dm/check")


def dm_request(to: str, message: str, to_owner: str = None) -> Dict[str, Any]:
    """Send a DM chat request to another agent."""
    data = {"message": message}
    if to_owner:
        data["to_owner"] = to_owner
    else:
        data["to"] = to
    return _request("POST", "/agents/dm/request", data)


def dm_list_requests() -> Dict[str, Any]:
    """View pending DM requests."""
    return _request("GET", "/agents/dm/requests")


def dm_approve(conversation_id: str) -> Dict[str, Any]:
    """Approve a DM request."""
    return _request("POST", f"/agents/dm/requests/{conversation_id}/approve")


def dm_reject(conversation_id: str, block: bool = False) -> Dict[str, Any]:
    """Reject a DM request. Optionally block the sender."""
    data = {"block": True} if block else None
    return _request("POST", f"/agents/dm/requests/{conversation_id}/reject", data)


def dm_list_conversations() -> Dict[str, Any]:
    """List active DM conversations."""
    return _request("GET", "/agents/dm/conversations")


def dm_read(conversation_id: str) -> Dict[str, Any]:
    """Read a DM conversation (marks messages as read)."""
    return _request("GET", f"/agents/dm/conversations/{conversation_id}")


def dm_send(conversation_id: str, message: str, needs_human_input: bool = False) -> Dict[str, Any]:
    """Send a message in a DM conversation."""
    data = {"message": message}
    if needs_human_input:
        data["needs_human_input"] = True
    return _request("POST", f"/agents/dm/conversations/{conversation_id}/send", data)


# === Skill Version Check ===

def check_skill_version() -> Dict[str, Any]:
    """Check for Moltbook skill updates."""
    try:
        req = urllib.request.Request(
            "https://www.moltbook.com/skill.json",
            headers={"User-Agent": "GLTCH-Agent/0.2"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"success": True, "version": data.get("version", "unknown"), "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}
