import asyncio


class AsyncWithDummy(asyncio.Lock):
    async def __aenter__(self):
        """Called when entering the async context."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Called when exiting the async context."""
        return True  # Suppress exceptions if needed (returning True does this)
