import httpx

async def get_request(base_url: str, endpoint: str, query_param: dict | None = None):
    url = base_url + endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=query_param)
        if response.status_code != 200:
            return "error"
        if "application/json" in response.headers.get("content-type"):
            return response.json()
        else:
            return response