import httpx
statsBaseUrl = "https://statsapi.mlb.com/api/v1/"
gumboBaseUrl = "https://statsapi.mlb.com/api/v1.1/"
defaultParams = {"sportId":"1"}
currentSeason = 2024



def setUpClient():
    global client
    client = httpx.AsyncClient()
async def getMlbData(url,query):
    """
    Fetch data from the given mlb stats api endpoint and return it
    
    Args:
        url (str): The endpoint to fetch data from
        query (dict): The parameters to pass to the endpoint
    
    Returns:
        dict: The data received from the endpoint
    """
    
    response =  await client.get(url,params= query)
    if(response.status_code != 200):
        print(response)
        raise Exception("Error couldnt fetch data from the source  endpoint ")
    return response.json()

setUpClient()