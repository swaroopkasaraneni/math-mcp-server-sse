from .server import serve


def main():
    """MCP Math Server - Maths functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to make web requests"
    )

    asyncio.run(serve())


if __name__ == "__main__":
    main()