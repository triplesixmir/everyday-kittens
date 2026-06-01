import aiohttp
from config import CAT_API_KEY

_API_URL = "https://api.thecatapi.com/v1/images/search"


async def fetch_random_kitten() -> str | None:
    headers = {"x-api-key": CAT_API_KEY} if CAT_API_KEY else {}
    params = {"mime_types": "jpg,png", "size": "med"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_API_URL, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data[0]["url"]
    except Exception:
        pass

    return None
