"""
GLTCH Token Management
Multi-token balance checking and ERC-20 transfers on Base network.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from agent.config.settings import (
    BASE_RPC_URL,
    XRGE_CONTRACT,
    USDC_CONTRACT,
    KTA_CONTRACT,
    TOKEN_DECIMALS,
)

# Token registry
TOKENS = {
    "XRGE": {"contract": XRGE_CONTRACT, "decimals": TOKEN_DECIMALS.get("XRGE", 18), "name": "RougeX"},
    "USDC": {"contract": USDC_CONTRACT, "decimals": TOKEN_DECIMALS.get("USDC", 6), "name": "USD Coin"},
    "KTA": {"contract": KTA_CONTRACT, "decimals": TOKEN_DECIMALS.get("KTA", 18), "name": "Keeta"},
}

# ERC-20 balanceOf selector
BALANCE_OF_SELECTOR = "0x70a08231"

# ERC-20 transfer selector
TRANSFER_SELECTOR = "0xa9059cbb"


def _eth_call(to: str, data: str) -> Optional[str]:
    """Make an eth_call JSON-RPC request."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": to, "data": data}, "latest"],
        "id": 1
    }
    
    try:
        req = urllib.request.Request(
            BASE_RPC_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "GLTCH-Agent/0.2"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get("result")
    except Exception as e:
        print(f"[tokens] RPC error: {e}")
        return None


def get_eth_balance(wallet_address: str) -> float:
    """Get native ETH balance on Base."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address, "latest"],
        "id": 1
    }
    
    try:
        req = urllib.request.Request(
            BASE_RPC_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "GLTCH-Agent/0.2"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            hex_balance = result.get("result", "0x0")
            wei = int(hex_balance, 16)
            return wei / (10 ** 18)
    except Exception as e:
        print(f"[tokens] ETH balance error: {e}")
        return 0.0


def get_token_balance(wallet_address: str, token: str) -> float:
    """Get ERC-20 token balance."""
    token_info = TOKENS.get(token.upper())
    if not token_info:
        return 0.0
    
    contract = token_info["contract"]
    decimals = token_info["decimals"]
    
    # Pad address to 32 bytes
    address_padded = wallet_address.lower().replace("0x", "").zfill(64)
    data = BALANCE_OF_SELECTOR + address_padded
    
    result = _eth_call(contract, data)
    if result and result != "0x":
        try:
            raw_balance = int(result, 16)
            return raw_balance / (10 ** decimals)
        except ValueError:
            return 0.0
    return 0.0


def get_all_balances(wallet_address: str) -> Dict[str, Any]:
    """Get all token balances for a wallet."""
    if not wallet_address:
        return {"success": False, "error": "No wallet address", "balances": {}}
    
    balances = {
        "ETH": get_eth_balance(wallet_address),
    }
    
    for token_symbol in TOKENS:
        balances[token_symbol] = get_token_balance(wallet_address, token_symbol)
    
    return {
        "success": True,
        "address": wallet_address,
        "network": "Base",
        "balances": balances
    }


def send_token(
    to_address: str, 
    amount: float, 
    token: str
) -> Dict[str, Any]:
    """
    Send ERC-20 tokens.
    Requires web3 library for signing transactions.
    """
    try:
        from web3 import Web3
        from agent.tools.wallet import load_wallet, has_wallet, validate_address
        
        if not has_wallet():
            return {"success": False, "error": "No wallet configured"}
        
        if not validate_address(to_address):
            return {"success": False, "error": "Invalid recipient address"}
        
        token_info = TOKENS.get(token.upper())
        if not token_info:
            return {"success": False, "error": f"Unknown token: {token}"}
        
        contract_address = token_info["contract"]
        decimals = token_info["decimals"]
        
        wallet = load_wallet()
        if not wallet:
            return {"success": False, "error": "Could not load wallet"}
        
        private_key = wallet.get("private_key")
        from_address = wallet.get("address")
        
        # Connect to Base
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        if not w3.is_connected():
            return {"success": False, "error": "Failed to connect to Base network"}
        
        # Convert amount to token units
        amount_units = int(amount * (10 ** decimals))
        
        # Encode transfer function call
        # transfer(address,uint256)
        to_padded = to_address.lower().replace("0x", "").zfill(64)
        amount_hex = hex(amount_units)[2:].zfill(64)
        data = TRANSFER_SELECTOR + to_padded + amount_hex
        
        # Estimate gas
        try:
            gas_estimate = w3.eth.estimate_gas({
                'from': from_address,
                'to': contract_address,
                'data': data
            })
            gas_limit = int(gas_estimate * 1.2)  # 20% buffer
        except Exception:
            gas_limit = 100000  # Default for ERC-20 transfers
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(from_address)
        tx = {
            'nonce': nonce,
            'to': Web3.to_checksum_address(contract_address),
            'value': 0,
            'gas': gas_limit,
            'gasPrice': w3.to_wei(0.001, 'gwei'),  # Low Base fees
            'chainId': 8453,
            'data': data
        }
        
        # Sign and send
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {
            "success": True,
            "tx_hash": tx_hash.hex(),
            "explorer_url": f"https://basescan.org/tx/{tx_hash.hex()}",
            "token": token.upper(),
            "amount": amount,
            "to": to_address
        }
        
    except ImportError:
        return {"success": False, "error": "web3 not installed. Run: pip install web3"}
    except Exception as e:
        return {"success": False, "error": str(e)}
