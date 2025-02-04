import asyncio
import functions_framework
from utils.database import init_db
from utils.player_data import save_player_data
from utils.team_data import save_team_data

eventLoop = asyncio.new_event_loop()
asyncio.set_event_loop(eventLoop)

async def main_func():
    await init_db()
    await save_player_data()
    await save_team_data()
    return "data saved"

@functions_framework.http
def http_function(request):
    return eventLoop.run_until_complete(main_func())