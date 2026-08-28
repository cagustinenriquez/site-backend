from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import posts

app = FastAPI(
    title="agustinenriquez.dev API",
    description="Backend API for agustinenriquez.dev blog",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(posts.router)


@app.get("/health")
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
