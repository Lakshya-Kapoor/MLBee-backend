from fastapi import APIRouter, HTTPException
from utils.setUpMlb import statsBaseUrl,defaultParams,currentSeason
from utils.request import get_request
from enum import Enum
import asyncio

router = APIRouter()

AmericanLeagueId = 103
NationalLeagueId = 104
class standingType(Enum):
    division = 'division'
    league = 'league'

id_to_name = {
    103: "AL",
    104: "NL",
    200: "AL_West",
    201: "AL_East",
    202: "AL_Central",
    203: "NL_West",
    204: "NL_East",
    205: "NL_Central"

}

requiredTeamInfo = ['team','streak','divisionRank','leagueRank','gamesPlayed','runsAllowed','runsScored','wins','losses','runDifferential','clinched']
# if the divison rank is not one but clinched = true then wildcard 
def formatTeamData(team) -> dict:
    """
    Format the team data for the standings.
    """
    teamData = {key:value for key,value in team.items() if key in requiredTeamInfo}
    teamData['teamId'] = teamData['team']['id']
    teamData['teamName'] = teamData['team']['name']
    teamData['streakCode'] = teamData['streak']['streakCode']
    del teamData['team']
    del teamData['streak']
    return teamData


def formatStandingDataDivisons(data) -> dict:
    return {id_to_name[record['division']['id']]:[formatTeamData(teamData) for teamData in record['teamRecords']] for record in data['records']}

def formatStandingDataLeague(data) -> dict:
    return  {id_to_name[data['records'][0]['league']['id']]:[formatTeamData(teamData) for teamData in data['records'][0]['teamRecords']]}

@router.get('/')
async def get_standings(season: int = 2025):
    """
    Endpoint to get MLB standings by league or division. By default, returns both league data.
    Specify American League by 103 and National League by 104.
    """
    query = {'season':season}
    query.update(defaultParams)

    al_league_data, al_division_data, nl_league_data, nl_division_data = await asyncio.gather(
        get_request(statsBaseUrl, f'/standings/byLeague', {**query, 'leagueId':AmericanLeagueId}), 
        get_request(statsBaseUrl, f'/standings/byDivision',{**query, 'leagueId':AmericanLeagueId}),
        get_request(statsBaseUrl, f'/standings/byLeague', {**query, 'leagueId':NationalLeagueId}), 
        get_request(statsBaseUrl, f'/standings/byDivision',{**query, 'leagueId':NationalLeagueId}))

    # return al_division_data
    
    league_res = {**formatStandingDataLeague(al_league_data), **formatStandingDataLeague(nl_league_data)}
    division_res = {**formatStandingDataDivisons(al_division_data), **formatStandingDataDivisons(nl_division_data)}

    for key in league_res.keys():
        league_res[key] = sorted(league_res[key], key=lambda x: int(x['leagueRank']))
    for key in division_res.keys():
        division_res[key] = sorted(division_res[key], key=lambda x: int(x['divisionRank']))

    return {**league_res, **division_res}