import asyncio
from functools import wraps


class AsyncWithDummy(asyncio.Lock):
    async def __aenter__(self):
        """Called when entering the async context."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Called when exiting the async context."""
        return True  # Suppress exceptions if needed (returning True does this)


def run_in_async_thread(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> None:
        # Run the function in a separate thread
        coro = asyncio.to_thread(func, *args, **kwargs)
        # Create and run the task asynchronously
        asyncio.create_task(coro)

    return wrapper
