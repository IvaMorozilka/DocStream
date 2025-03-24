import aiohttp
import os

API_ENDPOINT = os.environ.get("API_ENDPOINT")


async def upload_documnet_to_filestoarage(
    file_io: bytes,
    file_name: str,
    content_type: str,
    dashboard_name: str,
    api_url=API_ENDPOINT + "/upload_file/",
):
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field(
                name="file",
                value=file_io,
                filename=file_name,
                content_type=content_type,
            )

            params = {"dashboard_name": dashboard_name}

            async with session.post(api_url, data=data, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return False, result
                else:
                    error_text = await response.text()
                    return True, {
                        "error": f"400: {response.status}",
                        "details": error_text,
                    }
    except Exception as e:
        return True, {"error": str(e)}
