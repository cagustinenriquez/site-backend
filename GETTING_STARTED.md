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
