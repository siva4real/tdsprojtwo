import os
import time
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent
from shared_store import url_time, BASE64_STORE

load_dotenv()

# Load credentials from environment
EMAIL = os.getenv("EMAIL") 
SECRET = os.getenv("SECRET")

# Initialize FastAPI application
app = FastAPI()

# Configure CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track application startup time
START_TIME = time.time()

@app.get("/healthz")
def healthz():
    """Health check endpoint for service monitoring."""
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME)
    }

@app.post("/solve")
async def solve(request: Request, background_tasks: BackgroundTasks):
    """
    Main endpoint to trigger agent task solving.
    
    Validates request credentials, clears shared state, and launches
    the agent in a background task to avoid blocking the response.
    """
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    if not request_data:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Extract required fields
    task_url = request_data.get("url")
    auth_secret = request_data.get("secret")
    
    if not task_url or not auth_secret:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Validate authentication
    if auth_secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Reset shared state for new task
    url_time.clear() 
    BASE64_STORE.clear()  
    
    print("Verified starting the task...")
    
    # Initialize environment for agent
    os.environ["url"] = task_url
    os.environ["offset"] = "0"
    url_time[task_url] = time.time()
    
    # Launch agent in background
    background_tasks.add_task(run_agent, task_url)

    return JSONResponse(status_code=200, content={"status": "ok"})


if __name__ == "__main__":
    # Start server on all interfaces, port 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)