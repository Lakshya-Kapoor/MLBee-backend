from beanie import Document

class Team(Document):
    name: str
    team_id: int
    all_star_status: str
    location: str
    first_year_play: int
    league: str
    division: str
    logo: str | None

    class Settings:
        name = "teams"