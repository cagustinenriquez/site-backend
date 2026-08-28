# agustinenriquez.dev Backend

Backend API for [agustinenriquez.dev](https://agustinenriquez.dev), a personal blog and portfolio.

## Overview

This is a FastAPI-based backend providing RESTful APIs for managing blog posts and site content. Built with Python for agustinenriquez.dev.

## Stack

- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation

## Getting Started

For local development setup, see [GETTING_STARTED.md](./GETTING_STARTED.md).

## Documentation

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Installation and development setup
- **[API.md](./API.md)** - API endpoints and usage
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contribution guidelines

## Project Structure

```
site-backend/
├── main.py                # Application entry point
├── app/                   # Application code
│   ├── config.py          # Configuration
│   ├── models.py          # Pydantic models
│   └── routes/            # API route handlers
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── GETTING_STARTED.md     # Development setup guide
├── API.md                 # API documentation
└── CONTRIBUTING.md        # Contribution guidelines
```

## Quick Start

**Using pip:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Using uv (faster):**
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
python main.py
```

Access the API at `http://localhost:8000` and docs at `http://localhost:8000/docs`

## License

MIT License - see LICENSE file for details
