import uvicorn
import asyncio
from .server import server_run
def main():
    
    print("Starting MCP server 'Math' on 127.0.0.1:5000")
        # Use this approach to keep the server running
    #app.run(transport="sse")
    server_run()

if __name__ == "__main__":
    main()