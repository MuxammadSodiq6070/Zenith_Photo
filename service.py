import httpx
from os import getenv
from dotenv import load_dotenv
 
load_dotenv()

params = {
    'id': '24302596',
    'photo': 'https://cdnn21.img.ria.ru/images/07e7/09/0f/1896619602_0:162:3072:1890_1920x1080_80_0_0_a0e61740ef7ef4bc4edd7377b08654d9.jpg'
}

url = 'https://saverapi.net/api/photolab-api'
headers = {
    'x-api-key': getenv("SAVER_API_KEY"),
    'Content-Type': 'application/json'
}


async def get_photo_url():
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        result = response.json()
        return result.get("download_url", "error")

def sync_main():
    with httpx.Client() as client:
        response = client.get(url, params=params, headers=headers)
        result = response.json()
        return result.get("download_url", "error")
    

    
if __name__ == "__main__":
    sync_main()