#!/usr/bin/env python3
"""
Script to create a new user or reset admin password.

Usage:
    python scripts/create_user.py <username> <password>

Example:
    python scripts/create_user.py admin mypassword123
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.users import create_user, get_user


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_user.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    if get_user(username):
        print(f"Error: User '{username}' already exists")
        sys.exit(1)

    try:
        user = create_user(username, password)
        print(f"✓ User '{user.username}' created successfully")
    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
