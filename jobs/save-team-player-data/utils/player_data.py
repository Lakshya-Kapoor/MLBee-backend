from models.player import Player
from utils.request import get_request
from datetime import datetime

async def save_player_data():
    """
    Saves the player data to database
    First it fetches the team data from the MLB stats API
    Then saves selected info about the players to the database
    """

    await Player.delete_all()

    response = await get_request("https://statsapi.mlb.com", "/api/v1/sports/1/players", {"season": datetime.now().year})
    if response == "error":
        return "error"
    
    players = response["people"]
    players_data = []
    for player in players:
        player_id = player["id"]
        team_id = player["currentTeam"]["id"]
        name = player["fullName"]
        age = player["currentAge"]
        height = player["height"]
        weight = player["weight"]
        birth_city = player.get("birthCity", "")
        birth_country = player["birthCountry"]
        birth_place = f"{birth_city},{birth_country}"
       
        primary_number = player.get("primaryNumber", None)
        primary_position = player["primaryPosition"]["name"]
        bat_side = player["batSide"]["description"]
        pitch_hand = player["pitchHand"]["description"]
        image=f'https://securea.mlb.com/mlb/images/players/head_shot/{player_id}.jpg'
        
        players_data.append(Player(
            player_id=player_id,
            team_id=team_id,
            name=name,
            age=age,
            height=height,
            weight=weight,
            birth_place=birth_place,
            primary_number=primary_number,
            primary_position=primary_position,
            bat_side=bat_side,
            pitch_hand=pitch_hand,
            image=image
        ))

    await Player.insert_many(players_data)