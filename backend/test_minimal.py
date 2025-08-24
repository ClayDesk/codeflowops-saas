"""
Minimal test application to diagnose deployment issues
"""
from fastapi import FastAPI

app = FastAPI(title="Test Minimal API")

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "minimal test app working"}

@app.get("/")
async def root():
    return {"message": "Test API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
