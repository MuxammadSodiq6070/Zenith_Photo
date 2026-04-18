# service.py

import httpx
import logging
from os import getenv
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = "https://saverapi.net/api"
HEADERS = {
    "x-api-key": getenv("SAVER_API_KEY"),
    "Content-Type": "application/json",
}


# service.py — fetch_photolab ni tuzatish

async def fetch_photolab(photo_url: str, effect_id: str) -> dict:
    params = {"id": effect_id, "photo": photo_url}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{BASE_URL}/photolab-api",
                params=params,
                headers=HEADERS,
            )
            response.raise_for_status()
            
            # None kelishi mumkin, shuning uchun tekshiramiz
            result = response.json()
            if result is None:
                logger.error(f"API None qaytardi. Raw: {response.text}")
                return {"error": "empty_response", "download_url": None}
                
            logger.info(f"Photolab javobi: {result}")
            return result

    except httpx.TimeoutException:
        logger.error("Timeout")
        return {"error": "timeout", "download_url": None}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP xatosi: {e.response.status_code}")
        return {"error": f"http_{e.response.status_code}", "download_url": None}
    except Exception as e:
        logger.error(f"Xato: {e}")
        return {"error": str(e), "download_url": None}


async def get_download_url(photo_url: str, effect_id: str) -> str | None:
    result = await fetch_photolab(photo_url, effect_id)
    if not result or not isinstance(result, dict):
        return None
    return result.get("download_url")

async def get_download_url(photo_url: str, effect_id: str) -> str | None:
    """
    Faqat download_url ni qaytaradi. Xato bo'lsa None qaytaradi.
    """
    result = await fetch_photolab(photo_url, effect_id)
    return result.get("download_url")


async def get_multiple_effects(photo_url: str, effect_ids: list[str]) -> list[dict]:
    """
    Bir rasmga bir nechta effekt parallel ravishda qo'llaydi.
    """
    import asyncio
    tasks = [fetch_photolab(photo_url, eid) for eid in effect_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for eid, res in zip(effect_ids, results):
        if isinstance(res, Exception):
            output.append({"effect_id": eid, "error": str(res), "download_url": None})
        else:
            output.append({"effect_id": eid, **res})
    return output



def sync_fetch(photo_url: str, effect_id: str) -> dict:
    """Sinxron versiya — faqat test/debug uchun."""
    params = {"id": effect_id, "photo": photo_url}
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{BASE_URL}/photolab-api",
                params=params,
                headers=HEADERS,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Sync xato: {e}")
        return {"error": str(e), "download_url": None}


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    # Test
    result = asyncio.run(
        fetch_photolab(
            photo_url="https://cdnn21.img.ria.ru/images/07e7/09/0f/1896619602_0:162:3072:1890_1920x1080_80_0_0_a0e61740ef7ef4bc4edd7377b08654d9.jpg",
            effect_id="24302596",
        )
    )
    print(result)