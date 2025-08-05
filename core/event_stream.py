import asyncio
import json

listeners: list[asyncio.Queue] = []


def register() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    listeners.append(queue)
    return queue


def unregister(queue: asyncio.Queue) -> None:
    try:
        listeners.remove(queue)
    except ValueError:
        pass


async def broadcast(event: dict) -> None:
    if not listeners:
        return
    data = json.dumps(event)
    for queue in list(listeners):
        await queue.put(data)
