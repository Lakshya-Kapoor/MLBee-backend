from beanie import Document

class User(Document):
    username: str
    email: str
    password: str
    player_names: list[str] = []
    team_names: list[str] = []

    class Settings:
        name = "users"