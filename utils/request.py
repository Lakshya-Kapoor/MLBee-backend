import httpx


async def get_request(base_url: str, endpoint: str, query_param: dict | None = None):
    url = base_url + endpoint
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=query_param)
        if response.status_code != 200:
            print(response.json())
            return "error"
        if "application/json" in response.headers.get("content-type"):
            return response.json()
        else:
            print("Response type: ", response.headers.get("content-type"))
            return response