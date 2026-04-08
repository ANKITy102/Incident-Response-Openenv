# Hugging Face Spaces entry point
# This file redirects to the actual server app

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server.app import app
except ImportError:
    # Fallback for when running in different contexts
    import uvicorn
    from fastapi import FastAPI
    
    # Create a basic FastAPI app as fallback
    app = FastAPI(title="Incident Response Environment")
    
    @app.get("/")
    async def root():
        return {"message": "Incident Response Environment - Server module not found"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

# Export the app for Hugging Face Spaces
__all__ = ["app"]
