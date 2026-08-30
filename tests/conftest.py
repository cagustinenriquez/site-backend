import json
import shutil
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def reset_test_data():
    """Reset data/posts.json before each test to ensure isolation"""
    data_dir = Path("data")
    posts_file = data_dir / "posts.json"
    backup_file = data_dir / "posts.json.backup"

    # Backup original data
    if posts_file.exists() and not backup_file.exists():
        shutil.copy(posts_file, backup_file)

    # Reset to initial state before each test
    initial_data = {
        "welcome-to-my-blog": {
            "id": "1",
            "slug": "welcome-to-my-blog",
            "title": "Welcome to My Blog",
            "content": "This is the first blog post on agustinenriquez.dev. Here you'll find posts about web development, software engineering, and other tech topics I'm passionate about.",
            "excerpt": "Welcome to agustinenriquez.dev blog",
            "tags": ["welcome", "intro"],
            "date": "2026-08-28T00:00:00"
        }
    }

    data_dir.mkdir(exist_ok=True)
    with open(posts_file, "w") as f:
        json.dump(initial_data, f, indent=2)

    yield

    # Optionally restore after tests
    # (leaving this commented to preserve test data for inspection)
    # if backup_file.exists():
    #     shutil.copy(backup_file, posts_file)
