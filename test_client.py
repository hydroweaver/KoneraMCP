# from fastmcp import Client
# import asyncio
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

async def main():
    # The client will automatically handle Google OAuth
    async with Client("https://54d7bf2d3fe9.ngrok-free.app/mcp", auth="oauth") as client:
        # First-time connection will open Google login in your browser
        print("✓ Authenticated with Google!")
        
        # Test the protected tool
        result = await client.call_tool("get_user_info")
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())