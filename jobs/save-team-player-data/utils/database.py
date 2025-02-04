from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.player import Player
from models.team import Team


DB_URL = "mongodb+srv://laqshyakapoor:9wjIaIy56QM6sIUq@cluster0.wz0xh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

async def init_db():
    client = AsyncIOMotorClient(DB_URL)
    await init_beanie(client.mlb, document_models=[Player, Team])