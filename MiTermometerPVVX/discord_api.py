import httpx
from functools import wraps
import time
from env_settings import settings

# In-memory cache to track recently sent messages
_sent_messages_cache = {}
LIMIT_INTERVAL = 60 * 60 * 24
CLEANUP_INTERVAL = LIMIT_INTERVAL + 100


def limit_repeated_messages(interval: int, cleanup_interval: int = CLEANUP_INTERVAL):
    """
    Decorator to prevent sending the same message within a given time interval.
    Also performs periodic cleanup of old records.

    Args:
        interval (int): Time in seconds to block repeated messages.
        cleanup_interval (int): Time in seconds to trigger cleanup of stale records.
    """
    _last_cleanup_time = [
        time.time()
    ]  # Use a mutable object to store the last cleanup time

    def decorator(func):
        @wraps(func)
        async def wrapper(message: str, *args, **kwargs):
            nonlocal _last_cleanup_time
            current_time = time.time()

            # Perform cleanup if the cleanup interval has passed
            if current_time - _last_cleanup_time[0] > cleanup_interval:
                _cleanup_cache(current_time, interval)
                _last_cleanup_time[0] = current_time

            # Check if the message is rate-limited
            if message in _sent_messages_cache:
                last_sent_time = _sent_messages_cache[message]
                if current_time - last_sent_time < interval:
                    # Skip sending the message
                    print(f"Message '{message}' not sent (rate limited).")
                    return None

            # Update cache and proceed
            _sent_messages_cache[message] = current_time
            return await func(message, *args, **kwargs)

        return wrapper

    return decorator


def _cleanup_cache(current_time: float, interval: int):
    """
    Cleanup old entries in the cache that are beyond the defined interval.
    """
    global _sent_messages_cache
    keys_to_delete = [
        message
        for message, last_sent_time in _sent_messages_cache.items()
        if current_time - last_sent_time > interval
    ]
    for key in keys_to_delete:
        del _sent_messages_cache[key]
    print(f"Cleaned up {len(keys_to_delete)} stale entries from the cache.")


@limit_repeated_messages(interval=LIMIT_INTERVAL)
async def send_message(message: str, tts: bool = False) -> bool | None:
    web_hook = settings.DISCORD_WEB_HOOKS
    print(f"Sending message: {message} {web_hook=}")
    if not web_hook or not message:
        return None
    json = {
        "username": "atc-temp-bot",
        "avatar_url": "",
        "content": message,
        "tts": tts,
    }
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(web_hook, json=json, timeout=10)
    return response.status_code < 300


if __name__ == "__main__":
    import asyncio

    async def main():
        await send_message("Hello world!")  # Sent
        await send_message("Hello world!")  # Not sent (rate limited)
        await asyncio.sleep(61)  # Wait for rate limit to expire
        await send_message("Hello world!")  # Sent again

        # Trigger cleanup
        await asyncio.sleep(310)  # Wait for cleanup interval to pass
        await send_message("Hello again!")  # Sent

    asyncio.run(main())
