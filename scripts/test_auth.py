#!/usr/bin/env python3
"""
Test auth endpoints to diagnose issues.
Run this on PythonAnywhere to verify authentication is working.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.users import get_user, create_user, authenticate_user
from app.auth import verify_password, get_password_hash, verify_token, create_access_token
from app.config import DATA_DIR
from datetime import timedelta


def test_data_dir():
    """Test that DATA_DIR is configured correctly"""
    print(f"✓ DATA_DIR: {DATA_DIR}")
    print(f"✓ DATA_DIR exists: {DATA_DIR.exists()}")
    if DATA_DIR.exists():
        print(f"✓ Files in DATA_DIR: {list(DATA_DIR.glob('*'))}")
    return DATA_DIR.exists()


def test_users_json():
    """Test that users.json exists and is readable"""
    users_file = DATA_DIR / "users.json"
    print(f"\n✓ users.json path: {users_file}")
    print(f"✓ users.json exists: {users_file.exists()}")

    if users_file.exists():
        with open(users_file, "r") as f:
            users = json.load(f)
        print(f"✓ Users in file: {list(users.keys())}")
        return True
    return False


def test_get_user():
    """Test retrieving a user"""
    print("\n--- Testing get_user('admin') ---")
    user = get_user("admin")
    if user:
        print(f"✓ Found user: {user.username}")
        print(f"✓ Hashed password: {user.hashed_password[:30]}...")
        return True
    else:
        print("✗ User 'admin' not found")
        return False


def test_password_verification():
    """Test password verification"""
    print("\n--- Testing password verification ---")
    user = get_user("admin")
    if not user:
        print("✗ User not found, skipping")
        return False

    # Test with correct password
    correct = verify_password("adminJepeto32$$", user.hashed_password)
    print(f"✓ verify_password('adminJepeto32$$'): {correct}")

    # Test with wrong password
    wrong = verify_password("wrongpassword", user.hashed_password)
    print(f"✓ verify_password('wrongpassword'): {wrong}")

    return correct and not wrong


def test_authenticate_user():
    """Test the full authenticate_user flow"""
    print("\n--- Testing authenticate_user ---")

    # Test correct credentials
    user = authenticate_user("admin", "adminJepeto32$$")
    if user:
        print(f"✓ authenticate_user('admin', 'adminJepeto32$$'): Success")
    else:
        print(f"✗ authenticate_user('admin', 'adminJepeto32$$'): Failed")
        return False

    # Test wrong credentials
    user = authenticate_user("admin", "wrongpassword")
    if not user:
        print(f"✓ authenticate_user('admin', 'wrongpassword'): Correctly failed")
    else:
        print(f"✗ authenticate_user('admin', 'wrongpassword'): Should have failed")
        return False

    return True


def test_token_generation():
    """Test JWT token generation"""
    print("\n--- Testing token generation ---")

    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(minutes=30)
    )
    print(f"✓ Access token created: {access_token[:30]}...")

    # Verify token
    username = verify_token(access_token, token_type="access")
    if username == "admin":
        print(f"✓ Token verified: {username}")
        return True
    else:
        print(f"✗ Token verification failed: {username}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AUTH ENDPOINT DIAGNOSTIC TEST")
    print("=" * 60)

    tests = [
        ("DATA_DIR Configuration", test_data_dir),
        ("users.json File", test_users_json),
        ("Get User", test_get_user),
        ("Password Verification", test_password_verification),
        ("Full Authentication", test_authenticate_user),
        ("Token Generation", test_token_generation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(r for _, r in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
