# Deployment Guide - PythonAnywhere

Step-by-step guide to deploy the FastAPI backend on PythonAnywhere.

## Prerequisites

- PythonAnywhere account (free tier works)
- Project cloned on PythonAnywhere (already done on your account)
- Dependencies installed

## Deployment Steps

### 1. Verify Installation on PythonAnywhere

SSH into your PythonAnywhere bash console:

```bash
cd ~/site-backend

# Verify dependencies are installed
pip list | grep fastapi

# Run tests to confirm everything works
python3 -m pytest tests/ -v
```

### 2. Create Web App on PythonAnywhere Dashboard

1. Go to **PythonAnywhere Dashboard** → **Web** tab
2. Click **Add a new web app**
3. Select **Manual configuration** (not frameworks)
4. Choose **Python 3.13**

### 3. Configure WSGI File

1. In the **Web** tab, find your web app
2. Go to **WSGI configuration file** section
3. Update the WSGI file path:
   ```
   /home/agustinenriquez/site-backend/wsgi.py
   ```

The WSGI file should contain:
```python
import os
import sys

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from main import app
application = app
```

### 4. Configure Virtualenv

In the **Web** tab, set the **Virtualenv** path:
```
/home/agustinenriquez/site-backend/venv
```

(Or `.venv` if that's what you used)

### 5. Set Environment Variables

1. Go to the **Web** app settings
2. Scroll to **Web app** section
3. Add environment variables in the bash console:

```bash
# Set variables in your web app's environment
export SECRET_KEY="your-secret-key-here"
export ADMIN_PASSWORD="your-admin-password"
export DEBUG=false
```

Or in PythonAnywhere's web app settings if available.

### 6. Reload Web App

In the **Web** tab, click the green **Reload** button to restart your app.

### 7. Access Your API

Your API will be available at:
```
https://agustinenriquez.pythonanywhere.com
```

Test it:
```bash
curl https://agustinenriquez.pythonanywhere.com/health
curl https://agustinenriquez.pythonanywhere.com/docs
```

## Troubleshooting

### Issue: 502 Bad Gateway

Check the error log in **Web** tab → **Error log**

Common causes:
- WSGI path incorrect
- Virtualenv path incorrect
- Environment variables not set
- Dependencies not installed

**Solution:**
```bash
# Check logs
tail -50 /var/log/agustinenriquez.pythonanywhere.com.error.log

# Reinstall dependencies
cd ~/site-backend
pip install -r requirements.txt
```

### Issue: Module Not Found

```bash
cd ~/site-backend
source venv/bin/activate
pip install -e .
```

### Issue: Database/Data Directory

Ensure `data/` directory exists:
```bash
cd ~/site-backend
mkdir -p data
```

### Clear Cache

If changes don't appear, reload:
1. Click **Reload** in Web tab
2. Or in bash: `touch /var/www/agustinenriquez_pythonanywhere_com_wsgi.py`

## Production Checklist

Before going live:

- [ ] Change `SECRET_KEY` to something secure
- [ ] Change `ADMIN_PASSWORD`
- [ ] Set `DEBUG=false`
- [ ] Update CORS `allow_origins` to your domain
- [ ] Test all endpoints at https://agustinenriquez.pythonanywhere.com/docs
- [ ] Monitor error logs regularly

## API Usage

Once deployed:

### Get Authentication Token

```bash
curl -X POST https://agustinenriquez.pythonanywhere.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}'
```

### Create a Post

```bash
curl -X POST https://agustinenriquez.pythonanywhere.com/posts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is amazing!",
    "tags": ["test"]
  }'
```

### List Posts

```bash
curl https://agustinenriquez.pythonanywhere.com/posts
```

## Resources

- [PythonAnywhere Docs](https://help.pythonanywhere.com/)
- [FastAPI with WSGI](https://fastapi.tiangolo.com/deployment/concepts/#asgi)
- [API Documentation](./API.md)
- [Project Guide](./SKILLS.md)
