from fastapi import FastAPI
from contextlib import asynccontextmanager
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool, Prompt, PromptArgument, PromptMessage, GetPromptResult,
    TextContent, ErrorData, INVALID_PARAMS
)
from pydantic import BaseModel, Field
from typing import Annotated
from fastapi import Request

server = Server("math-mcp")
sse = SseServerTransport("/messages/")

class MathOperation(BaseModel):
    a: Annotated[int, Field(description="First number")]
    b: Annotated[int, Field(description="Second number")]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register handlers here
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="add", description="Add two numbers", inputSchema=MathOperation.model_json_schema()),
            Tool(name="multiply", description="Multiply two numbers", inputSchema=MathOperation.model_json_schema()),
        ]

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
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name, arguments):
        a = arguments.get("a")
        b = arguments.get("b")
        if name == "add":
            result = a + b
            return GetPromptResult(
                description=f"{a} + {b}",
                messages=[
                    PromptMessage(role="user", content=TextContent(type="text", text=f"What is {a} + {b}?")),
                    PromptMessage(role="assistant", content=TextContent(type="text", text=f"{a} + {b} = {result}")),
                ]
            )
        elif name == "multiply":
            result = a * b
            return GetPromptResult(
                description=f"{a} * {b}",
                messages=[
                    PromptMessage(role="user", content=TextContent(type="text", text=f"What is {a} * {b}?")),
                    PromptMessage(role="assistant", content=TextContent(type="text", text=f"{a} * {b} = {result}")),
                ]
            )
        raise ErrorData(code=-32601, message="Prompt not found")

    @server.call_tool()
    async def call_tool(name, arguments: dict) -> list[TextContent]:
        try:
            args = MathOperation(**arguments)
        except Exception as e:
            raise ErrorData(code=INVALID_PARAMS, message=str(e))
        
        if name == "add":
            result = args.a + args.b
        elif name == "multiply":
            result = args.a * args.b
        else:
            raise ErrorData(code=INVALID_PARAMS, message="Unknown tool")
        return [TextContent(type="text", text=f"Result: {result}")]

    yield  # Everything's initialized

# Initialize FastAPI with lifespan hook
app = FastAPI(lifespan=lifespan)

# SSE POST endpoint
app.mount("/messages/", sse.handle_post_message)

# SSE connection endpoint
@app.get("/sse")
async def sse_get(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())

# Extra: HTTP GET endpoint for test harness
@app.get("/tools/list")
async def tools_list():
    return await server._handlers["list_tools"]()
