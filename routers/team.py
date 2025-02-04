from fastapi import APIRouter, Depends, HTTPException
from models.team import Team
from models.player import Player
from models.user import User
from utils.request import get_request
from datetime import datetime
from utils.constants import STATS_BASE_URL, battingStats, fieldingStats, pitchingStats
from utils.middleware import get_current_user
import asyncio

router = APIRouter()

@router.get("/")
async def get_teams(name: str | None = None, id: int | None = None, limit: int = 5):
    query = {}

    if name is not None:
        query["name"] = {"$regex": name, "$options": "i"}
    if id is not None:
        query["team_id"] = id
    
    teams = await Team.find(query).to_list()
    return teams[:limit]    

@router.get("/follows")
async def get_followed_teams(user: dict = Depends(get_current_user)):
    user_res = await User.find_one(User.username == user['username'])
    return user_res.team_names

@router.get("/{team_id}/roster")
async def get_team_roster(team_id: int):
    players = await Player.find({"team_id": team_id}).to_list()
    return players


@router.get("/{team_id}/stats")
async def get_team_stats(team_id: int):
    currentSeason = datetime.now().year - 1
    path = f"/api/v1/teams/{team_id}/stats"
    query = {'stats': 'SEASON', 'season': currentSeason, 'group': ["HITTING", "PITCHING", "FIELDING"]}
    data = await get_request(STATS_BASE_URL, path, query)
    teamStatsAll = {statData['group']['displayName']: statData['splits'][0]['stat'] for statData in data['stats']}
    teamStats = {}
    for statType, stats in teamStatsAll.items():
        if statType == "pitching":
            focusedStat = pitchingStats
        elif statType == "fielding":
            focusedStat = fieldingStats
        else:
            focusedStat = battingStats
        teamStats[statType] = {stat: value for stat, value in teamStatsAll[statType].items() if stat in focusedStat}
    return teamStats

@router.get("/{team_id}/follow")
async def is_followed(team_id: int, user: dict = Depends(get_current_user)):
    user_task = User.find_one(User.username == user['username'])
    team_task = Team.find_one(Team.team_id == team_id)

    user_res, team_res = await asyncio.gather(user_task, team_task)

    return {"following" :team_res.name in user_res.team_names}

@router.post("/{team_id}/follow")
async def follow_unfollow_team(team_id: int, follow: bool, user: dict = Depends(get_current_user)):
    user_task = User.find_one(User.username == user['username'])
    team_task = Team.find_one(Team.team_id == team_id)

    user_res, team_res = await asyncio.gather(user_task, team_task)

    if follow:
        if team_res.name not in user_res.team_names:
            user_res.team_names.append(team_res.name)
            await user_res.save()
            return {"message": "Team followed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Team already followed")
    else:
        if team_res.name in user_res.team_names:
            user_res.team_names.remove(team_res.name)
            await user_res.save()
            return {"message": "Team unfollowed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Team not followed")
