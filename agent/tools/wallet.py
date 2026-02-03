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
