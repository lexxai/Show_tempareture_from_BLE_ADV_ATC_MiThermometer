import httpx

from env_settings import settings


async def send_message(message: str, tts: bool = False) -> bool | None:
    web_hook = settings.DISCORD_WEB_HOOKS
    if not web_hook or not message:
        return None
    json = {
        "username": "fastparking",
        "avatar_url": "",
        "content": message,
        "tts": tts,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(web_hook, json=json, timeout=10)
    return response.status_code < 300


if __name__ == "__main__":
    import asyncio

    asyncio.run(send_message("Hello world!"))
