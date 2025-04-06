from typing import Annotated
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.types import (
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
)
from pydantic import BaseModel, Field
from mcp.server.sse import SseServerTransport

from starlette.responses import Response
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# ---------------------------------------------
# Models
# ---------------------------------------------
class MathOperation(BaseModel):
    a: Annotated[int, Field(description="First number")]
    b: Annotated[int, Field(description="Second number")]

# ---------------------------------------------
# Shared Server & Transport Instances
# ---------------------------------------------
server = Server("math-mcp")
sse = SseServerTransport("/messages/")

# ---------------------------------------------
# Lifespan
# ---------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Place to add init/cleanup logic if needed later
    yield

# ---------------------------------------------
# App Factory
# ---------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # Register CORS if needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register endpoints
    @app.get("/sse")
    async def sse_handler(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())
        return Response(status_code=200)

    app.mount("/messages", sse.handle_post_message)

    return app

# ---------------------------------------------
# MCP Handlers
# ---------------------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="add", description="Adds two numbers.", inputSchema=MathOperation.model_json_schema()),
        Tool(name="multiply", description="Multiplies two numbers.", inputSchema=MathOperation.model_json_schema()),
    ]

@server.get_prompt()
async def get_prompt(name, arguments):
    a = arguments.get("a")
    b = arguments.get("b")

    if name == "multiply":
        result = a * b
        return GetPromptResult(
            description=f"Multiply {a} * {b}",
            messages=[
                PromptMessage(role="user", content=TextContent(type="text", text=f"What is {a} * {b}?")),
                PromptMessage(role="assistant", content=TextContent(type="text", text=f"{a} * {b} = {result}")),
            ]
        )
    elif name == "add":
        result = a + b
        return GetPromptResult(
            description=f"Add {a} + {b}",
            messages=[
                PromptMessage(role="user", content=TextContent(type="text", text=f"What is {a} + {b}?")),
                PromptMessage(role="assistant", content=TextContent(type="text", text=f"{a} + {b} = {result}")),
            ]
        )

    raise ErrorData(code=-32601, message="Prompt not found")

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="add",
            description="Adds two numbers",
            arguments=[
                PromptArgument(name="a", description="First number", required=True),
                PromptArgument(name="b", description="Second number", required=True),
            ]
        ),
        Prompt(
            name="multiply",
            description="Multiplies two numbers",
            arguments=[
                PromptArgument(name="a", description="First number", required=True),
                PromptArgument(name="b", description="Second number", required=True),
            ]
        )
    ]

@server.call_tool()
async def call_tool(name, arguments: dict) -> list[TextContent]:
    try:
        args = MathOperation(**arguments)
    except ValueError as e:
        raise ErrorData(code=INVALID_PARAMS, message=str(e))

    if name == "add":
        result = args.a + args.b
    elif name == "multiply":
        result = args.a * args.b
    else:
        raise ErrorData(code=INVALID_PARAMS, message="Unknown operation")

    return [TextContent(type="text", text=f"Result: {result}")]

# ---------------------------------------------
# Expose app for uvicorn
# ---------------------------------------------
app = create_app()
