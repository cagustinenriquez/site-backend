#!/usr/bin/env python3
"""Test if hashes survive JSON serialization"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import get_password_hash, verify_password
from app.config import DATA_DIR

password = "adminJepeto32$$"

# Create hash
hash1 = get_password_hash(password)
print(f"Created hash: {hash1}")
print(f"Verify immediately: {verify_password(password, hash1)}")

# Save to JSON
data = {"test": {"hash": hash1}}
json_str = json.dumps(data, indent=2)
print(f"\nJSON string:\n{json_str}")

# Load from JSON
loaded = json.loads(json_str)
hash2 = loaded["test"]["hash"]
print(f"\nLoaded hash: {hash2}")
print(f"Hashes match: {hash1 == hash2}")
print(f"Verify loaded: {verify_password(password, hash2)}")

# Check byte by byte
if hash1 != hash2:
    print("\n⚠️  Hashes differ!")
    for i, (c1, c2) in enumerate(zip(hash1, hash2)):
        if c1 != c2:
            print(f"  Position {i}: '{c1}' vs '{c2}'")
