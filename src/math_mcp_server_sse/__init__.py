import uvicorn

def main():
    """MCP Math Server - SSE Transport Math Server"""
    uvicorn.run("math_mcp_server_sse.server:app", host="0.0.0.0", port=5000, reload=True)

if __name__ == "__main__":
    main()
