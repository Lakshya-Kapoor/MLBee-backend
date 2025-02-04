from models.team import Team
from utils.request import get_request
from datetime import datetime

async def save_team_data():
    """
    Saves the team data to database
    First it fetches the team data from the MLB stats API
    Then saves selected info about the teams to the database
    """

    # Deletes all previosly saved team data
    await Team.delete_all()
    
    response = await get_request("https://statsapi.mlb.com", "/api/v1/teams",{"sportIds": 1, "season": datetime.now().year})
    if response == "error":
        return "error"
    
    teams = response["teams"]

    teams_data = []

    for team in teams:
        name = team["name"]
        team_id = team["id"]
        all_start_status = team["allStarStatus"]
        location = team["locationName"]
        first_year_play = team["firstYearOfPlay"]
        league = team["league"]["name"]
        division = team["division"]["name"]
        logo = f"https://www.mlbstatic.com/team-logos/{team_id}.svg"

        teams_data.append(Team(name=name, team_id=team_id, all_star_status=all_start_status, location=location, first_year_play=first_year_play, league=league, division=division, logo=logo))

    await Team.insert_many(teams_data)