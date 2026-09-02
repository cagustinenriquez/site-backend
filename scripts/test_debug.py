#!/usr/bin/env python3
"""Debug password verification issue"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.users import get_user
from app.auth import verify_password
from app.config import DATA_DIR

# Read hash from file
users_file = DATA_DIR / "users.json"
with open(users_file, "r") as f:
    users = json.load(f)

admin_data = users["admin"]
stored_hash = admin_data["hashed_password"]

print(f"Stored hash type: {type(stored_hash)}")
print(f"Stored hash length: {len(stored_hash)}")
print(f"Stored hash: {stored_hash}")
print(f"Hash starts with: {stored_hash[:20]}")
print(f"Hash ends with: {stored_hash[-20:]}")

# Try to verify
password = "adminJepeto32$$"
result = verify_password(password, stored_hash)
print(f"\nverify_password('{password}', stored_hash) = {result}")

# Also test through get_user
print("\n--- Testing through get_user ---")
user = get_user("admin")
if user:
    print(f"User hash: {user.hashed_password}")
    result2 = verify_password(password, user.hashed_password)
    print(f"Result: {result2}")
