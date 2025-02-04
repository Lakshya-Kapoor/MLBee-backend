from fastapi import APIRouter, Depends, HTTPException
from utils.setUpMlb import statsBaseUrl,defaultParams,currentSeason
from utils.request import get_request
from models.player import Player
from models.team import Team
from models.user import User
from utils.middleware import get_current_user
from utils.constants import battingStats, fieldingStats, pitchingStats, focusedPlayerInfo
import asyncio
router = APIRouter()

@router.get("/")
async def get_players(name: str | None = None, id: int | None = None, limit: int = 5):
    query = {}

    if name is not None:
        query["name"] = {"$regex": name, "$options": "i"}
    if id is not None:
        query["player_id"] = id
    
    players = await Player.find(query).to_list()
    response = []
    for player in players:
        team = await Team.find_one({"team_id": player.team_id})
        player_data = player.model_dump()
        player_data["team_name"] = team.name
        player_data["team_logo"] = team.logo
        response.append(player_data)
    
    return response[:limit]


@router.get("/{player_id}/stats")
async def getPlayerStastsById(player_id: int):      
    """
    endpoint returns the filtered stats for the player_id provided from the mlb website 
    filtered stats are divided into hitting, pitching and fielding
    """
    path = f"people/{player_id}/stats"
    query = {'stats': 'season', 'season': currentSeason, 'group': ['hitting', 'pitching', 'fielding']}
    query.update(defaultParams)
    data = await get_request(statsBaseUrl, path, query)
    playerStatsAll = {statData['group']['displayName']: statData['splits'][0]['stat'] for statData in data['stats']}
    playerStats = {}
    for statType, stats in playerStatsAll.items():
        if statType == "pitching":
            focusedStat = pitchingStats
        elif statType == "fielding":
            focusedStat = fieldingStats
        else:
            focusedStat = battingStats
        playerStats[statType] = {stat: value for stat, value in playerStatsAll[statType].items() if stat in focusedStat}
    return playerStats

@router.get('/info')
async def getPlayerInfoById(playerId:int):
    """
    endpoint returns the filtered information for the playerId provided from the mlb website 
    filtered info contains player's nickname, jersey number, age, birth country, height, primary position, batting hand and pitching hand
    """
    path = f"people/{playerId}"
    query = {}
    query.update(defaultParams)
    data = await get_request(statsBaseUrl, path, query)
    playerInfo = {infoType: info for infoType, info in data['people'][0].items() if infoType in focusedPlayerInfo}
    playerInfo['primaryPosition'] = playerInfo['primaryPosition']['name'] + '-' + playerInfo['primaryPosition']['type']
    playerInfo['batSide'] = playerInfo['batSide']['description']
    playerInfo['pitchHand'] = playerInfo['pitchHand']['description']
    return playerInfo

@router.get('/search')
async def getPlayerIdByName(playerName:str):
    """
    Endpoint to search for players by name.
    This function searches for players using the given player name and returns
    a dictionary mapping player IDs to their full names from the MLB website.
    """
    path = 'people/search'
    query = {'seasons': [currentSeason], 'names': [playerName]}
    query.update(defaultParams)
    data = await get_request(statsBaseUrl, path, query)
    playerIds = {player['id']: player['fullName'] for player in data['people']}
    return playerIds

@router.get('/overview')
async def getPlayerOverviewById(playerId:int):
    """
    Endpoint to get an overview of a player by their id.
    This endpoint returns a dictionary with three keys:
    'team', 'league', and 'player'. Each value is a dictionary containing the name and id of the respective object.
    """
    path = f"people/{playerId}/stats"
    query = {'stats': 'season', 'season': currentSeason}
    query.update(defaultParams)
    data = await get_request(statsBaseUrl, path, query)
    team = {infoType: info for infoType, info in data['stats'][0]['splits'][0]['team'].items() if infoType in {'name', 'id'}}
    league = {infoType: info for infoType, info in data['stats'][0]['splits'][0]['league'].items() if infoType in {'name', 'id'}}
    player = {infoType: info for infoType, info in data['stats'][0]['splits'][0]['player'].items() if infoType in {'fullName', 'id'}}
    return {'team': team, 'league': league, 'player': player}

@router.get("/{player_id}/follow")
async def is_followed(player_id: int, user: dict = Depends(get_current_user)):
    user_task = User.find_one(User.username == user['username'])
    player_task = Player.find_one(Player.player_id == player_id)

    user_res, player_res = await asyncio.gather(user_task, player_task)

    return {"following": player_res.name in user_res.player_names}

@router.post("/{player_id}/follow")
async def follow_unfollow_player(player_id: int, follow: bool, user: dict = Depends(get_current_user)):
    user_task = User.find_one(User.username == user['username'])
    player_task = Player.find_one(Player.player_id == player_id)

    user_res, player_res = await asyncio.gather(user_task, player_task)

    if follow:
        if player_res.name not in user_res.player_names:
            user_res.player_names.append(player_res.name)
            await user_res.save()
            return {"message": "Player followed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Player already followed")
    else:
        if player_res.name in user_res.player_names:
            user_res.player_names.remove(player_res.name)
            await user_res.save()
            return {"message": "Player unfollowed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Player not followed")