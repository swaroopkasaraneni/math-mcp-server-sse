from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Annotated

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
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel, Field

app: FastAPI = None  # Global for Uvicorn

server = Server("math-mcp")
sse = SseServerTransport("/messages/")


class MathOperation(BaseModel):
    """Parameters for math operations."""
    a: Annotated[int, Field(description="First number")]
    b: Annotated[int, Field(description="Second number")]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="add",
            description="Adds two numbers.",
            inputSchema=MathOperation.model_json_schema(),
        ),
        Tool(
            name="multiply",
            description="Multiplies two numbers.",
            inputSchema=MathOperation.model_json_schema(),
        ),
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
                PromptArgument(name="a", description="first number", required=True),
                PromptArgument(name="b", description="second number", required=True)
            ],
        ),
        Prompt(
            name="multiply",
            description="Multiplies two numbers",
            arguments=[
                PromptArgument(name="a", description="first number", required=True),
                PromptArgument(name="b", description="second number", required=True)
            ],
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do async startup here (e.g., preloading, db connections)
    yield
    # Do async cleanup here if needed


def create_app() -> FastAPI:
    global app
    app = FastAPI(lifespan=lifespan)

    # SSE endpoint
    @app.get("/sse")
    async def sse_endpoint(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())

    # POST message handling
    app.mount("/messages/", sse.handle_post_message)

    # ✅ Add HTTP endpoint for /tools/list
    @app.get("/tools/list")
    async def tools_list():
        tools = await list_tools()
        return JSONResponse(content=[tool.model_dump() for tool in tools])

    return app


app = create_app()
