# Username + Password Authentication Setup

## Overview

The backend now supports username + password authentication instead of just a hardcoded admin password. User credentials are stored in a JSON file (`data/users.json`) and validated against hashed passwords.

## Files Changed

### 1. **app/users.py** (NEW)
Handles user management:
- `get_user(username)` - Retrieve user by username
- `authenticate_user(username, password)` - Validate credentials
- `create_user(username, password)` - Create new user with hashed password

Users stored in `data/users.json`:
```json
{
  "admin": {
    "username": "admin",
    "hashed_password": "$2b$12$..."
  }
}
```

### 2. **app/routes/auth.py** (UPDATED)
- `LoginRequest` model now accepts `username` and `password`
- `/login` endpoint validates against user table instead of hardcoded password
- JWT token includes username in `sub` claim

### 3. **app/auth.py** (UPDATED)
- Removed `ADMIN_PASSWORD` environment variable (no longer needed)
- Core token generation logic unchanged

## Usage

### Create a New User

```bash
python scripts/create_user.py <username> <password>
```

Example:
```bash
python scripts/create_user.py admin secretpassword123
```

### Login

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secretpassword123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

- **access_token**: Use for API requests (expires in 30 minutes)
- **refresh_token**: Use to get new access token (expires in 7 days)

### Use Access Token in Requests

```bash
curl -X GET http://localhost:8000/posts \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Access Token (No Re-login Needed)

When your access token expires (after 30 minutes), use the refresh token to get a new one:

**Request:**
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

You can repeat this process for up to 7 days without re-entering your password.

## Migration from Old System

If you were using the old `ADMIN_PASSWORD` environment variable:

1. Remove `ADMIN_PASSWORD` from `.env` or environment variables
2. Create users with the new script:
   ```bash
   python scripts/create_user.py admin <old-password>
   ```
3. Users can now log in with username + password

## Data Storage

User credentials are stored in `data/users.json` by default:
- Passwords are hashed using Argon2 (never stored in plain text)
- File is automatically created when first user is added
- Ensure `data/` directory is backed up and not committed with actual passwords

### Configurable Data Directory (for PythonAnywhere)

For **PythonAnywhere** deployment, store the data directory outside the web root:

**In `.env`:**
```
DATA_DIR=/home/username/mysite/private_data
```

**Or create `/etc/systemd/system/myapp.service`:**
```
Environment="DATA_DIR=/home/username/private_data"
```

The app will:
1. Create the directory if it doesn't exist
2. Store `users.json` there instead of in the web-accessible `data/` folder
3. Keep your credentials completely private

## Security Notes

- Passwords are hashed with bcrypt before storage
- JWT tokens expire after 30 minutes by default
- Always use HTTPS in production
- Rotate your `SECRET_KEY` in environment variables
