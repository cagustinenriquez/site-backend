# Getting Started

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
  - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cagustinenriquez/site-backend.git
   cd site-backend
   ```

2. **Install dependencies**

   Using uv (recommended):
   ```bash
   uv sync            # app + dev dependencies (pytest, httpx)
   uv sync --no-dev   # app dependencies only
   ```
   This creates `.venv/` and installs the exact versions pinned in `uv.lock`,
   using the Python version from `.python-version` (uv downloads it if needed).
   Prefix commands with `uv run` (e.g. `uv run pytest`) instead of activating the venv.

   Using pip:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Adding or updating dependencies** (uv)
   ```bash
   uv add <package>          # runtime dependency
   uv add --dev <package>    # dev-only dependency
   uv lock --upgrade         # upgrade all within constraints
   ```
   Commit both `pyproject.toml` and `uv.lock`. If you change dependencies,
   regenerate `requirements.txt` for pip users:
   `uv export --no-hashes --no-emit-project -o requirements.txt`

4. **Environment Setup**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   APP_NAME="agustinenriquez.dev API"
   APP_VERSION="1.0.0"
   DEBUG=true
   DATABASE_URL="sqlite:///./blog.db"
   ```

## Development

### Start the development server

```bash
uv run python main.py   # or: python main.py (with venv activated)
```

Or using uvicorn directly:
```bash
uv run uvicorn main:app --reload
```

The server will start at `http://localhost:8000` with automatic reload enabled.

### Access API documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Run tests

```bash
uv run pytest   # or: make test
```

Watch mode:
```bash
pytest --watch
```

## Running with Docker

Requires Docker with the Compose plugin.

```bash
cp .env.example .env     # set SECRET_KEY and ADMIN_PASSWORD
make docker-up           # or: docker compose up -d --build
```

The API runs at http://localhost:8000. On startup the container applies database
migrations (`alembic upgrade head`) and then starts the API. Data is stored
wherever `DATABASE_URL` points (see [Database](#database-supabase)). Without it,
a SQLite file in the `posts-data` volume is used.

```bash
make docker-logs         # follow logs
make docker-down         # stop (data is kept)
docker compose down -v   # stop and delete the posts volume
```

The image installs only runtime dependencies from `uv.lock` and runs as a
non-root user. `.env` is never copied into the image; it's passed at runtime.

**Creating a user:** run the script inside the running container, so it uses the
same `DATABASE_URL`. Once a user exists, `admin` + `ADMIN_PASSWORD` stops working:

```bash
docker compose exec api python scripts/create_user.py <username> <password>
```

**Behind a reverse proxy** (nginx, Traefik, Cloudflare, ...): rate limits are
per client IP, so uvicorn must trust the proxy's `X-Forwarded-For` header or
every request will appear to come from the proxy. Add the proxy's IP (or `*` if
the container is only reachable through the proxy) to `.env`:

```bash
FORWARDED_ALLOW_IPS=*
```

## Database (Supabase)

All data (posts, users, recruiters) lives in a SQL database. The app reaches
it one of two ways:

- **`DATABASE_URL`**: a direct database connection. Locally it defaults to a
  SQLite file (`data/app.db`). In Docker or on a paid host it's Supabase's
  Postgres.
- **`SUPABASE_URL` + `SUPABASE_KEY`**: Supabase's REST API over HTTPS, for hosts
  that block database connections, such as PythonAnywhere's free plan. See
  [Deploying to PythonAnywhere](#deploying-to-pythonanywhere). When both are set,
  this wins over `DATABASE_URL`.

Migrations and the JSON import always need a direct `DATABASE_URL`
connection, so run them from your own machine.

1. **Get the connection string:** in the Supabase dashboard, open your project,
   click **Connect**, and copy the **Session pooler** URI. It looks like:
   ```
   postgresql://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
   Use the session pooler rather than the "Direct connection": the direct host
   is IPv6-only on most plans, and Docker usually has no IPv6. Replace
   `[YOUR-PASSWORD]` with your database password (Project Settings → Database
   → reset it there if you don't know it). If the password has special
   characters such as `@`, `:` or `/`, URL-encode them.

2. **Put it in `.env`** as `DATABASE_URL=...`. It's a secret, so never commit it.

3. **Create the tables:**
   ```bash
   make migrate                 # or: uv run alembic upgrade head
   ```
   The Docker container also does this on every start. The migration turns on
   Row Level Security for every table, so Supabase's public REST API (the
   `anon` key) can't read or write them. Only this backend can.

4. **Import the old JSON data** (optional, safe to run more than once):
   ```bash
   make import-data             # reads data/posts.json, users.json, recruiters.json
   # In Docker, where users.json lives in the posts-data volume:
   docker compose exec api python scripts/import_json_data.py
   ```

**Changing tables:** edit `app/db_models.py`, then generate and check a migration:
```bash
uv run alembic revision --autogenerate -m "describe the change"
```
`tests/test_db.py` fails if the models and migrations don't match.

**Tests** use an in-memory SQLite database and never touch `DATABASE_URL` or
Supabase. To also run them against Postgres and through the Supabase REST
backend, start a local Postgres + PostgREST (the server behind Supabase's REST
API). Their tables are wiped by the tests:
```bash
docker compose -f docker-compose.test.yml up -d
make test-pg      # direct Postgres connection
make test-rest    # Supabase REST backend
docker compose -f docker-compose.test.yml down -v
```

## Deploying to PythonAnywhere

Free accounts can't open database connections, but they can reach
`*.supabase.co` over HTTPS, so the app uses Supabase's REST API there.

1. **Get the API key:** in Supabase, open **Project Settings → API Keys** and
   copy the **secret** key (`sb_secret_...`), or the legacy `service_role`
   key. It bypasses Row Level Security, so it must only live on the server.

2. **Get the code and a Python 3.10 virtualenv** in a PythonAnywhere Bash
   console. The pinned packages don't install on Python 3.13:
   ```bash
   cd ~/site-backend && git fetch && git checkout main && git pull
   mkvirtualenv --python=python3.10 site-backend
   pip install -r requirements.txt
   ```

3. **Create `~/site-backend/.env`** with at least:
   ```
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_KEY=sb_secret_...
   SECRET_KEY=<long random string>
   ```
   `.env` is read from the project folder, whatever directory the app runs from.

4. **Web tab:**
   - Python version **3.10**.
   - Virtualenv `/home/<username>/.virtualenvs/site-backend`.
   - Replace the WSGI configuration file's contents with:
     ```python
     import sys
     sys.path.insert(0, "/home/<username>/site-backend")
     from wsgi import application  # noqa
     ```

   Then click **Reload**.

5. **Check it:** `https://<username>.pythonanywhere.com/health` should return
   `{"status": "ok"}`, and `/posts` should list your posts from Supabase.

Tables are created and changed from your own machine (`make migrate` with
`DATABASE_URL`). To add a user on PythonAnywhere, run
`python scripts/create_user.py <username> <password>` in the project folder,
with the virtualenv active.

## Project Structure

```
├── main.py               # Application entry point
├── app/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic models
│   └── routes/
│       ├── __init__.py
│       └── posts.py      # Blog posts endpoints
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## Troubleshooting

### Port already in use
If port 8000 is already in use, specify a different port:
```bash
uvicorn main:app --reload --port 8001
```

### Virtual environment issues
Ensure the virtual environment is activated before installing dependencies:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### ModuleNotFoundError
Ensure all dependencies are installed:
```bash
uv sync   # or: pip install -r requirements.txt
```

## Next Steps

- Read the [API documentation](./API.md) to understand the available endpoints
- Check out the [CONTRIBUTING.md](./CONTRIBUTING.md) guide before submitting changes
