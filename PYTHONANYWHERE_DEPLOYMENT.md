# PythonAnywhere Deployment Guide

Complete setup instructions for deploying the blog backend with username + password authentication on PythonAnywhere.

## Prerequisites

- PythonAnywhere account (free or paid)
- Git repository access
- SSH access to PythonAnywhere (paid account)

## Step 1: Clone Repository

1. Open PythonAnywhere **Bash Console**
2. Clone your repository:
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/site-backend.git
cd site-backend
```

## Step 2: Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 site-backend
pip install -r requirements.txt
```

## Step 3: Create Private Data Directory

Create a directory **outside the web root** for storing sensitive data:

```bash
mkdir -p ~/mysite/private_data
chmod 700 ~/mysite/private_data
```

## Step 4: Configure Environment Variables

Create `.env` file in your project root:

```bash
cd ~/site-backend
nano .env
```

Add these values:

```env
# Authentication
SECRET_KEY=your-secret-key-here-use-a-random-string
DATA_DIR=/home/YOUR_USERNAME/mysite/private_data

# Application
DEBUG=False
DATABASE_URL=sqlite:////home/YOUR_USERNAME/site-backend/blog.db

# Optional: Other configuration
APP_NAME=agustinenriquez.dev API
```

**To generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the file (Ctrl+X, then Y, then Enter in nano).

## Step 5: Create Admin User

Create your first admin user:

```bash
cd ~/site-backend
source /home/YOUR_USERNAME/.virtualenvs/site-backend/bin/activate
python scripts/create_user.py admin your-password-here
```

You'll see:
```
✓ User 'admin' created successfully
```

Check that the file was created in the private directory:
```bash
cat /home/YOUR_USERNAME/mysite/private_data/users.json
```

You should see your hashed password (NOT plain text).

## Step 6: Configure Web App

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** → **Python 3.10**

### Web App Settings

1. **Source code:** `/home/YOUR_USERNAME/site-backend`
2. **Working directory:** `/home/YOUR_USERNAME/site-backend`
3. **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/site-backend`

## Step 7: Configure WSGI File

In PythonAnywhere, edit the **WSGI configuration file**:

1. Go to **Web** tab
2. Click the WSGI file link (e.g., `/var/www/your_username_pythonanywhere_com_wsgi.py`)
3. Replace content with:

```python
import sys
import os
from pathlib import Path

# Add project to path
project_home = '/home/YOUR_USERNAME/site-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Set environment variables
os.environ.setdefault('SECRET_KEY', 'your-secret-key')
os.environ.setdefault('DATA_DIR', '/home/YOUR_USERNAME/mysite/private_data')
os.environ.setdefault('DEBUG', 'False')

# Import and run FastAPI
from main import app as application
```

## Step 8: Configure Static/Media Files

In **Web** tab, add these URL mappings:

| URL           | Directory                                |
|---------------|------------------------------------------|
| `/static/`    | `/home/YOUR_USERNAME/site-backend/static`|

(Leave empty if you don't have static files)

## Step 9: Test the Deployment

1. Reload the web app in PythonAnywhere
2. Visit `https://YOUR_DOMAIN.pythonanywhere.com/`
3. Test the API:

```bash
curl https://YOUR_DOMAIN.pythonanywhere.com/health
```

Should return:
```json
{"status": "ok"}
```

## Step 10: Test Authentication

### Login
```bash
curl -X POST https://YOUR_DOMAIN.pythonanywhere.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password-here"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Use Token
```bash
curl -H "Authorization: Bearer <access_token>" \
  https://YOUR_DOMAIN.pythonanywhere.com/posts
```

## Security Checklist

- [ ] `users.json` is in `/home/YOUR_USERNAME/mysite/private_data`
- [ ] Directory permissions: `chmod 700 /home/YOUR_USERNAME/mysite/private_data`
- [ ] `.env` file is NOT in `.gitignore` ignored properly
- [ ] `SECRET_KEY` is a random 32+ character string
- [ ] `DEBUG=False` in production
- [ ] HTTPS is enabled (PythonAnywhere handles this)
- [ ] `users.json` is backed up regularly

## Create Additional Users

After deployment, create more users via PythonAnywhere console:

```bash
cd ~/site-backend
source /home/YOUR_USERNAME/.virtualenvs/site-backend/bin/activate
python scripts/create_user.py username new-password
```

## Troubleshooting

### "404 Not Found" on any endpoint
- Check **Web** tab → reload web app
- Check error log in PythonAnywhere dashboard

### "Invalid authentication credentials"
- Verify user exists: `cat /home/YOUR_USERNAME/mysite/private_data/users.json`
- Check username and password are correct
- Try creating a new user

### "Permission denied" accessing data directory
```bash
chmod 700 /home/YOUR_USERNAME/mysite/private_data
chmod 600 /home/YOUR_USERNAME/mysite/private_data/users.json
```

### Environment variables not loading
- Make sure `.env` file exists in project root
- Check `.env` syntax (no spaces around `=`)
- Reload web app after changes

### "users.json not found"
- Create the directory: `mkdir -p /home/YOUR_USERNAME/mysite/private_data`
- Create a user: `python scripts/create_user.py admin password`

## Accessing Logs

In PythonAnywhere dashboard:
- **Server log** shows request/response info
- **Error log** shows Python errors
- **Access log** shows all HTTP requests

## Backup and Restore

### Backup users data
```bash
cp /home/YOUR_USERNAME/mysite/private_data/users.json ~/users.json.backup
```

### Restore users data
```bash
cp ~/users.json.backup /home/YOUR_USERNAME/mysite/private_data/users.json
chmod 600 /home/YOUR_USERNAME/mysite/private_data/users.json
```

## Update Application

When you push new code to GitHub:

1. SSH into PythonAnywhere
2. Pull latest code:
```bash
cd ~/site-backend
git pull origin main
```

3. Install any new dependencies:
```bash
source /home/YOUR_USERNAME/.virtualenvs/site-backend/bin/activate
pip install -r requirements.txt
```

4. Reload web app in PythonAnywhere dashboard

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | JWT signing key | `your-random-32-char-string` |
| `DATA_DIR` | User data storage directory | `/home/user/mysite/private_data` |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | SQLite database path | `sqlite:////home/user/site-backend/blog.db` |

## Quick Reference

**Directory structure:**
```
/home/USERNAME/
├── site-backend/                    # Project code
│   ├── app/
│   ├── data/                        # Posts (web-accessible, safe)
│   ├── scripts/
│   ├── .env                         # Environment config
│   └── requirements.txt
└── mysite/private_data/             # Sensitive data (NOT web-accessible)
    └── users.json                   # User credentials
```

**Common commands:**
```bash
# Create user
python scripts/create_user.py username password

# View users
cat /home/USERNAME/mysite/private_data/users.json

# View logs
tail -f /var/log/YOUR_DOMAIN_pythonanywhere_com_server.log

# Reload app
# Go to Web tab and click "Reload"
```

## Support

For PythonAnywhere help: https://help.pythonanywhere.com
For API documentation: `https://YOUR_DOMAIN.pythonanywhere.com/docs`
