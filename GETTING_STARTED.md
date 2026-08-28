# Getting Started

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cagustinenriquez/site-backend.git
   cd site-backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

   Activate it:
   - **Windows**: `venv\Scripts\activate`
   - **macOS/Linux**: `source venv/bin/activate`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

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
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000` with automatic reload enabled.

### Access API documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Run tests

```bash
pytest
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
pip install -r requirements.txt
```

## Next Steps

- Read the [API documentation](./API.md) to understand the available endpoints
- Check out the [CONTRIBUTING.md](./CONTRIBUTING.md) guide before submitting changes
