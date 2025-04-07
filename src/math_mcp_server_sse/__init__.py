import uvicorn
import asyncio
from .server import app
def main():
    
    print("Starting MCP server 'Math' on 127.0.0.1:5000")
        # Use this approach to keep the server running
    app.run(ransport="sse")

if __name__ == "__main__":
    main()