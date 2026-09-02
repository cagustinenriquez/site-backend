#!/usr/bin/env python3
"""Test password hashing directly"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import get_password_hash, verify_password

password = "adminJepeto32$$"

print("Testing password hashing...")
print(f"Original password: {password}")

# Hash it
hashed = get_password_hash(password)
print(f"Hashed: {hashed}")

# Verify it
verified = verify_password(password, hashed)
print(f"Verification result: {verified}")

if verified:
    print("✓ Hashing works!")
else:
    print("✗ Hashing FAILED!")
