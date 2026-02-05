
import sys
import os
import json
from pathlib import Path

print("Testing Wallet Generation...")
try:
    from eth_account import Account
    print("✓ eth-account imported")
    
    account = Account.create()
    print(f"✓ Account created: {account.address}")
    
    # Test saving
    test_file = Path("test_wallet.json")
    with open(test_file, 'w') as f:
        json.dump({"address": account.address}, f)
    print("✓ File write successful")
    
    # Clean up
    test_file.unlink()
    print("✓ File delete successful")
    
    print("\nSUCCESS: Wallet system is operational.")

except ImportError as e:
    print(f"\nERROR: Import failed - {e}")
except Exception as e:
    print(f"\nERROR: Validation failed - {e}")
    import traceback
    traceback.print_exc()
