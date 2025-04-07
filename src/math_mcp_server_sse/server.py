# math_server.py
from mcp.server.fastmcp import FastMCP
import time
import signal
import sys

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("Shutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

app = FastMCP(
    name="Math",
    host="0.0.0.0",
    port=5000,
    # Add this to make the server more resilient
    timeout=30  # Increase timeout to 30 seconds
)

@app.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@app.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

