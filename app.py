# Hugging Face Spaces entry point
# This file redirects to the actual server app

from server.app import app

# Export the app for Hugging Face Spaces
__all__ = ["app"]
