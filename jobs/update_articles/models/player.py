from beanie import Document

class Player(Document):
    name: str
    player_id: int
    age: int | None
    height: str | None
    weight: int | None
    birth_place: str | None
    primary_number: int | None
    primary_position: str | None
    bat_side: str | None
    pitch_hand: str | None
    image: str | None

    class Settings:
        name = "players"