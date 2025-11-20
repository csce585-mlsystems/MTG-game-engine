"""
Main entry point for the MTG Land Simulation API
"""
import uvicorn
from app.api import app

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="127.0.0.1", # May need to be changed to "localhost"
        port=8000,
        reload=True,
        log_level="info"
    )
