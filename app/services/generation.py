import asyncio
from typing import AsyncGenerator, Dict, List


async def stream_generate(prompt: str, contexts: List[Dict], tools: Dict) -> AsyncGenerator[str, None]:
# Simulate token streaming
    text = "[MOCK] " + prompt[:64]
    for token in text.split():
        await asyncio.sleep(0.05)
    yield token + " "


    if tools.get("projects"):
      yield "\nTop Projects (mock):\n"
    for row in tools["projects"]:
     yield f"- {row['id']} :: {row['name']} (priority {row['priority']})\n"