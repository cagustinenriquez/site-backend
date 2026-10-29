from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limiter import limiter
from app.routes import posts, auth, recruiters

app = FastAPI(
    title="agustinenriquez.dev API",
    description="Backend API for agustinenriquez.dev blog",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting: default limit on every route, 429 when exceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(recruiters.router)


@app.get("/health")
@limiter.exempt
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "ok"})


@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to agustinenriquez.dev API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
