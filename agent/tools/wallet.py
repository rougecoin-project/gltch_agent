"""
GLTCH Wallet Module
Generate and manage BASE network wallets
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Wallet storage path
WALLET_FILE = Path(__file__).parent.parent.parent / "wallet.json"


def generate_wallet() -> Dict[str, str]:
    """
    Generate a new Ethereum/BASE wallet.
    Returns dict with address and private_key.
    """
    try:
        from eth_account import Account
        
        # Generate new account
        account = Account.create()
        
        return {
            "address": account.address,
            "private_key": account.key.hex(),
            "network": "base"
        }
    except ImportError:
        raise ImportError("eth-account not installed. Run: pip install eth-account")


def import_wallet(private_key: str) -> Dict[str, str]:
    """
    Import wallet from private key.
    Returns dict with address and private_key.
    """
    try:
        from eth_account import Account
        
        # Normalize key format
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        # Validate and derive address from private key
        try:
            account = Account.from_key(private_key)
        except Exception:
            raise ValueError("Invalid private key format")
        
        wallet_data = {
            "address": account.address,
            "private_key": private_key,
            "network": "base"
        }
        
        # Save to file
        save_wallet(wallet_data)
        
        return wallet_data
    except ImportError:
        raise ImportError("eth-account not installed. Run: pip install eth-account")


def save_wallet(wallet_data: Dict[str, str], encrypt: bool = True) -> bool:
    """
    Save wallet to secure file.
    Private key is stored - handle with care!
    """
    try:
        # Create wallet file with restricted permissions
        with open(WALLET_FILE, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        # Set file permissions (read/write owner only)
        if os.name != 'nt':  # Unix
            os.chmod(WALLET_FILE, 0o600)
        
        return True
    except Exception as e:
        print(f"Error saving wallet: {e}")
        return False


def load_wallet() -> Optional[Dict[str, str]]:
    """Load wallet from file."""
    try:
        if WALLET_FILE.exists():
            with open(WALLET_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading wallet: {e}")
    return None


def delete_wallet() -> bool:
    """Delete wallet file."""
    try:
        if WALLET_FILE.exists():
            WALLET_FILE.unlink()
        return True
    except Exception as e:
        print(f"Error deleting wallet: {e}")
        return False


def get_wallet_address() -> Optional[str]:
    """Get wallet address without exposing private key."""
    wallet = load_wallet()
    return wallet.get("address") if wallet else None


def has_wallet() -> bool:
    """Check if wallet exists."""
    return WALLET_FILE.exists()


def export_wallet() -> Optional[Dict[str, str]]:
    """
    Export wallet data (includes private key!).
    Use with caution.
    """
    return load_wallet()


def get_private_key() -> Optional[str]:
    """
    Get private key for signing transactions.
    Handle with extreme care!
    """
    wallet = load_wallet()
    return wallet.get("private_key") if wallet else None


def format_address(address: str, short: bool = True) -> str:
    """Format address for display."""
    if not address:
        return ""
    if short:
        return f"{address[:6]}...{address[-4:]}"
    return address


def validate_address(address: str) -> bool:
    """Validate Ethereum address format."""
    if not address:
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


def send_transaction(to_address: str, amount_eth: float, gas_price_gwei: float = None) -> Dict[str, Any]:
    """
    Send ETH/BASE to another address.
    
    Args:
        to_address: Recipient address
        amount_eth: Amount in ETH to send
        gas_price_gwei: Optional gas price in Gwei (auto if None)
        
    Returns:
        Dict with tx_hash on success, or error message
    """
    try:
        from eth_account import Account
        from web3 import Web3
        
        # Validate recipient
        if not validate_address(to_address):
            return {"success": False, "error": "Invalid recipient address"}
        
        # Load wallet
        wallet = load_wallet()
        if not wallet:
            return {"success": False, "error": "No wallet configured"}
        
        private_key = wallet.get("private_key")
        from_address = wallet.get("address")
        
        # Connect to BASE RPC
        # Using public Base RPC endpoint
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        
        if not w3.is_connected():
            return {"success": False, "error": "Failed to connect to BASE network"}
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(from_address)
        
        # Convert amount to Wei
        value_wei = w3.to_wei(amount_eth, 'ether')
        
        # Check balance
        balance = w3.eth.get_balance(from_address)
        if balance < value_wei:
            return {
                "success": False, 
                "error": f"Insufficient balance. Have {w3.from_wei(balance, 'ether'):.6f} ETH"
            }
        
        # Build transaction
        tx = {
            'nonce': nonce,
            'to': Web3.to_checksum_address(to_address),
            'value': value_wei,
            'gas': 21000,  # Standard ETH transfer
            'gasPrice': w3.to_wei(gas_price_gwei or 0.001, 'gwei'),  # BASE has very low fees
            'chainId': 8453,  # BASE mainnet
        }
        
        # Sign transaction
        signed = w3.eth.account.sign_transaction(tx, private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {
            "success": True,
            "tx_hash": tx_hash.hex(),
            "explorer_url": f"https://basescan.org/tx/{tx_hash.hex()}",
            "amount": amount_eth,
            "to": to_address,
        }
        
    except ImportError as e:
        missing = "web3" if "web3" in str(e) else "eth-account"
        return {"success": False, "error": f"{missing} not installed. Run: pip install {missing}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
