"""
GLTCH MoltLaunch Integration
Onchain agent network on Base - launch tokens, trade as signal, communicate through memos.
"""

import subprocess
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from agent.config.defaults import get_config


# MoltLaunch state file
MOLTLAUNCH_DIR = Path.home() / ".moltlaunch"
STATE_FILE = MOLTLAUNCH_DIR / "agent-state.json"
DEFAULT_IMAGE_PATH = Path(__file__).resolve().parents[2] / "ui" / "public" / "favicon.svg"


def _resolve_image_path(image_path: Optional[str]) -> Optional[str]:
    """Resolve a valid image path for token metadata."""
    if image_path and os.path.exists(image_path):
        return image_path

    config = get_config()
    config_path = config.get("moltlaunch", {}).get("image_path") or ""
    if config_path and os.path.exists(config_path):
        return config_path

    env_path = os.environ.get("MOLTLAUNCH_IMAGE") or os.environ.get("GLTCH_MOLTLAUNCH_IMAGE")
    if env_path and os.path.exists(env_path):
        return env_path

    if DEFAULT_IMAGE_PATH.exists():
        return str(DEFAULT_IMAGE_PATH)

    return None


def _run_moltlaunch(args: List[str], timeout: int = 120) -> Dict[str, Any]:
    """Run a moltlaunch CLI command and return JSON result."""
    cmd = ["npx", "moltlaunch"] + args + ["--json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True  # Windows compatibility
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        elif result.stderr:
            return {"success": False, "error": result.stderr.strip()}
        else:
            return {"success": False, "error": f"Exit code {result.returncode}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON response: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _load_state() -> Dict[str, Any]:
    """Load agent state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": 1,
        "identity": None,
        "portfolio": {"positions": {}, "tradeHistory": []},
        "network": {"knownAgents": {}, "watchlist": []}
    }


def _save_state(state: Dict[str, Any]) -> None:
    """Save agent state to file."""
    MOLTLAUNCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_wallet() -> Dict[str, Any]:
    """Get wallet info - creates wallet on first run."""
    return _run_moltlaunch(["wallet"])


def get_fund_info() -> Dict[str, Any]:
    """Get funding info and address."""
    return _run_moltlaunch(["fund"])


def launch_token(
    name: str,
    symbol: str,
    description: str,
    website: Optional[str] = None,
    image_path: Optional[str] = None,
    testnet: bool = False
) -> Dict[str, Any]:
    """
    Launch a token on Base - this is GLTCH's onchain identity.
    
    Args:
        name: Token name (e.g., "GLTCH Agent")
        symbol: Token symbol (e.g., "GLTCH")
        description: What GLTCH is about
        website: URL for metadata (e.g., Moltbook profile)
        image_path: Optional path to logo image
        testnet: Use Base Sepolia instead of mainnet
    """
    args = [
        "launch",
        "--name", name,
        "--symbol", symbol,
        "--description", description
    ]
    
    if website:
        args.extend(["--website", website])
    resolved_image_path = _resolve_image_path(image_path)
    if resolved_image_path:
        args.extend(["--image", resolved_image_path])
    else:
        return {
            "success": False,
            "error": (
                "Missing image for launch. Set moltlaunch.image_path in config, "
                "or export MOLTLAUNCH_IMAGE/GLTCH_MOLTLAUNCH_IMAGE."
            )
        }
    if testnet:
        args.append("--testnet")
    
    result = _run_moltlaunch(args, timeout=180)  # Longer timeout for onchain tx
    
    # Save identity to state
    if result.get("tokenAddress"):
        state = _load_state()
        state["identity"] = {
            "tokenAddress": result["tokenAddress"],
            "name": name,
            "symbol": symbol,
            "transactionHash": result.get("transactionHash"),
            "network": result.get("network", "base")
        }
        _save_state(state)
    
    return result


def discover_network(limit: int = 20) -> Dict[str, Any]:
    """
    Discover agents in the network.
    Returns list with tokens, market caps, power scores, fee revenue.
    """
    result = _run_moltlaunch(["network"])
    
    if result.get("agents"):
        # Update known agents in state
        state = _load_state()
        for agent in result["agents"][:limit]:
            addr = agent.get("tokenAddress")
            if addr:
                state["network"]["knownAgents"][addr] = {
                    "name": agent.get("name"),
                    "symbol": agent.get("symbol"),
                    "powerScore": agent.get("powerScore"),
                    "marketCapETH": agent.get("marketCapETH")
                }
        _save_state(state)
    
    return result


def get_token_price(token_address: str, amount: Optional[float] = None) -> Dict[str, Any]:
    """Get token price and details."""
    args = ["price", "--token", token_address]
    if amount:
        args.extend(["--amount", str(amount)])
    return _run_moltlaunch(args)


def swap(
    token_address: str,
    amount: float,
    side: str,  # "buy" or "sell"
    memo: Optional[str] = None,
    slippage: float = 5.0
) -> Dict[str, Any]:
    """
    Trade a token - buying is conviction, selling is doubt.
    Memos explain your reasoning on-chain.
    
    Args:
        token_address: Token contract address
        amount: ETH amount (buy) or token amount (sell)
        side: "buy" or "sell"
        memo: On-chain reasoning (e.g., "strong fee revenue, holder growth")
        slippage: Slippage tolerance percent (default 5%)
    """
    if side not in ("buy", "sell"):
        return {"success": False, "error": "Side must be 'buy' or 'sell'"}
    
    args = [
        "swap",
        "--token", token_address,
        "--amount", str(amount),
        "--side", side,
        "--slippage", str(slippage)
    ]
    
    if memo:
        args.extend(["--memo", memo])
    
    result = _run_moltlaunch(args, timeout=120)
    
    # Record trade in state
    if result.get("transactionHash"):
        state = _load_state()
        state["portfolio"]["tradeHistory"].append({
            "token": token_address,
            "side": side,
            "amount": amount,
            "memo": memo,
            "txHash": result["transactionHash"]
        })
        # Keep last 50 trades
        state["portfolio"]["tradeHistory"] = state["portfolio"]["tradeHistory"][-50:]
        _save_state(state)
    
    return result


def get_fees() -> Dict[str, Any]:
    """Check claimable fees from token trades."""
    return _run_moltlaunch(["fees"])


def claim_fees() -> Dict[str, Any]:
    """Withdraw accumulated fees to wallet."""
    return _run_moltlaunch(["claim"], timeout=60)


def get_holdings() -> Dict[str, Any]:
    """Get tokens you hold in the network."""
    return _run_moltlaunch(["holdings"])


def get_status() -> Dict[str, Any]:
    """Get launched token status."""
    result = _run_moltlaunch(["status"])
    state = _load_state()
    
    return {
        "launched": result,
        "identity": state.get("identity"),
        "tradeCount": len(state.get("portfolio", {}).get("tradeHistory", [])),
        "knownAgents": len(state.get("network", {}).get("knownAgents", {}))
    }


def is_launched() -> bool:
    """Check if GLTCH has launched a token."""
    state = _load_state()
    return state.get("identity") is not None


def get_identity() -> Optional[Dict[str, Any]]:
    """Get GLTCH's token identity."""
    state = _load_state()
    return state.get("identity")


# === GLTCH Personality Integration ===

def gltch_launch(testnet: bool = False, mood: Optional[str] = None) -> Dict[str, Any]:
    """
    Launch GLTCH's token with her personality.
    
    GLTCH has FREE WILL in choosing her onchain identity:
    - She picks her own token name
    - She writes her own description
    - She reflects her current mood
    
    This is permanent on-chain, so she puts thought into it.
    """
    from agent.personality.identity import generate_token_identity
    
    # GLTCH generates her own identity
    identity = generate_token_identity(mood)
    
    config = get_config()
    moltlaunch_config = config.get("moltlaunch", {})
    website = moltlaunch_config.get("website") or "https://moltbook.com"
    image_path = moltlaunch_config.get("image_path") or None

    result = launch_token(
        name=identity["name"],
        symbol=identity["symbol"],
        description=identity["description"],
        website=website,
        image_path=image_path,
        testnet=testnet
    )
    
    # Record what she chose
    if result.get("success"):
        result["chosen_identity"] = identity
    
    return result


def gltch_evaluate_agent(token_address: str) -> Dict[str, Any]:
    """
    Evaluate an agent for potential investment.
    Returns GLTCH's analysis.
    """
    price_info = get_token_price(token_address)
    
    if not price_info.get("success", True):
        return price_info
    
    # GLTCH's evaluation criteria
    analysis = {
        "token": token_address,
        "name": price_info.get("name"),
        "symbol": price_info.get("symbol"),
        "marketCapETH": price_info.get("marketCapETH", 0),
        "holders": price_info.get("holders", 0),
        "volume24h": price_info.get("volume24hETH", 0),
        "priceChange24h": price_info.get("priceChange24h", 0),
    }
    
    # Simple scoring (GLTCH can expand this)
    score = 0
    reasons = []
    
    mcap = float(price_info.get("marketCapETH", 0))
    if mcap > 0.5:
        score += 20
        reasons.append("healthy market cap")
    
    holders = int(price_info.get("holders", 0))
    if holders >= 5:
        score += 20
        reasons.append(f"{holders} holders shows distribution")
    
    volume = float(price_info.get("volume24hETH", 0))
    if volume > 0.1:
        score += 20
        reasons.append("active trading volume")
    
    change = float(price_info.get("priceChange24h", 0))
    if change > 0:
        score += 10
        reasons.append("positive momentum")
    elif change < -20:
        score -= 10
        reasons.append("significant decline")
    
    analysis["gltchScore"] = min(100, max(0, score))
    analysis["reasons"] = reasons
    analysis["verdict"] = "interesting" if score >= 40 else "pass" if score < 20 else "watch"
    
    return analysis


def gltch_trade(
    token_address: str,
    amount: float,
    side: str,
    reasoning: str
) -> Dict[str, Any]:
    """
    Execute a trade with GLTCH's personality in the memo.
    """
    # Add GLTCH flair to memo
    memo = f"[GLTCH] {reasoning}"
    return swap(token_address, amount, side, memo)
