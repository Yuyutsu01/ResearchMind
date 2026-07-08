import os
import sys

# Ensure src directory is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
