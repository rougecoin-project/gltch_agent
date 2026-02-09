"""
GLTCH Token Gating Tool
Lightweight JSON-RPC implementation for Base (Ethereum L2) checks.
No web3.py dependency required.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Union

from agent.config.settings import BASE_RPC_URL, XRGE_CONTRACT, XRGE_GATE_THRESHOLD

# ERC-20 function signatures
FUNC_BALANCE_OF = "0x70a08231"  # balanceOf(address)


def _rpc_call(method: str, params: list, id: int = 1) -> Any:
    """Make a raw JSON-RPC call to the Base node."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": id
    }
    
    try:
        req = urllib.request.Request(
            BASE_RPC_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "GLTCH-Agent/0.2"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if "error" in data:
                print(f"[TokenGate] RPC Error: {data['error']}")
                return None
            return data.get("result")
            
    except Exception as e:
        print(f"[TokenGate] Connection Error: {str(e)}")
        return None


def get_token_balance(wallet_address: str, token_address: str = XRGE_CONTRACT) -> float:
    """
    Get ERC-20 token balance for a wallet.
    Returns balance as float (assuming 18 decimals).
    """
    if not wallet_address or not token_address:
        return 0.0
        
    # Remove '0x' prefix for padding
    clean_addr = wallet_address[2:] if wallet_address.startswith("0x") else wallet_address
    
    # Pad to 64 chars (32 bytes)
    padded_addr = clean_addr.zfill(64)
    
    # Construct data field: method_id + padded_address
    data = FUNC_BALANCE_OF + padded_addr
    
    # eth_call params: [{to: contract, data: data}, "latest"]
    result = _rpc_call("eth_call", [{"to": token_address, "data": data}, "latest"])
    
    if result and result != "0x":
        # Decode hex to int
        raw_balance = int(result, 16)
        # Assume 18 decimals for standard ERC-20
        return raw_balance / 10**18
        
    return 0.0


def check_access(feature: str, wallet_address: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if a wallet has access to a gated feature.
    If wallet_address is not provided, it should be retrieved from agent memory (caller responsibility).
    """
    if not wallet_address:
        return {
            "allowed": False,
            "reason": "No wallet connected",
            "balance": 0.0,
            "required": XRGE_GATE_THRESHOLD
        }
    
    # Verify XRGE balance
    if feature in ("unhinged", "code"):
        balance = get_token_balance(wallet_address, XRGE_CONTRACT)
        allowed = balance >= XRGE_GATE_THRESHOLD
        
        return {
            "allowed": allowed,
            "reason": "Insufficient XRGE balance" if not allowed else "Access granted",
            "balance": balance,
            "required": XRGE_GATE_THRESHOLD
        }
        
    # Default: allow non-gated features
    return {"allowed": True, "reason": "Feature not gated", "balance": 0, "required": 0}
