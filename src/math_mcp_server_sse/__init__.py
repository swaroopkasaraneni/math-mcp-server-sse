from .server import create_app
import uvicorn

def main():
    """MCP Math Server - SSE Transport Math Server"""
    uvicorn.run(create_app(), host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
