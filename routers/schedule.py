from fastapi import APIRouter
from utils.setUpMlb import statsBaseUrl,defaultParams,currentSeason,getMlbData,client
from enum import Enum

router = APIRouter()
requiredInfo = ['gamePk','gameType','gameDate','status','teams']


class GameState(Enum):
    live = "live"
    past = "past"
    future = "future"


# info of status codes dont delete 
# statusCodes = {
#     'S':'Scheduled to happen',
#     'P':'Match Starting soon',
#     'I':'is live or is haulted',
#     'M':'is live manager challenged',
#     'N':'is live umpire took an review',
#     'D':'is postponed',
#     'C':'cancelled',
#     'O':'game is completed',
#     'F':'game is completed',
#     'T':'suspended',
#     'U':'suspended',
#     'Q':'forfiet',
#     'U':'forfiet'
# }

async def getGameTypes() -> dict:
    """ get game Types from Mlb api  """
    path = 'gameTypes'
    response = await getMlbData(statsBaseUrl+path,{})
    data = {gameType['id']:gameType['description'] for gameType in response}
    return data 

def filterRevelantKeys(data) -> list:
    """
    Filter out the relevant information from the given data and return a list of dictionaries
    each containing the relevant information of a game.
    """
    schedule = []
    for date in data['dates']:
        for game in date['games']:
            schedule.append({infoType:info for infoType,info in game.items() if infoType in requiredInfo })
    return schedule

def formatScheduleData(data,gameTypes) -> list:
    

    """
    Format the schedule data by filtering out the relevant information,
    adding team names and ids, and adding the game type details.
    """
    schedule = filterRevelantKeys(data)
    
    for game in schedule:

        game['statusCode'] = game['status']['codedGameState']
        game['statusDetails'] = game['status']['detailedState'] 
        
        if('reason' in game['status']): 
            game['statusDetails'] += '-'+game['status']['reason']
        
        game['homeTeam'] = game['teams']['home']['team']['name']
        game['homeTeamId'] = game['teams']['home']['team']['id']
        game['awayTeam'] = game['teams']['away']['team']['name']
        game['awayTeamId'] = game['teams']['away']['team']['id']
        game['gameTypeDetails'] =  gameTypes[game['gameType']]
        
        if(game['statusCode'] in ['I','M','N','O','F','T','U']):
            game['awayTeamScore'] =  game['teams']['away']['score']
            game['homeTeamScore'] =  game['teams']['home']['score']
        
        if(game['statusCode'] in ['O','F']):
            game['tied'] = True if game['status']['statusCode'] in ['FT','FW','OT','OW'] else False
            if('isWinner' not in game['teams']['home']):
                game['winner'] = None
            elif(game['teams']['home']['isWinner']):
                game['winner'] = 'home'
            else:
                game['winner'] = 'away'
        
        del game['status']
        del game['teams']

    
    return schedule

@router.get('/')
async def getSchedule(teamId:int|None=None,gameState:GameState|None = None, season: int = 2025) -> list:
    
    """
    endpoint returs the schedule optional parameters are teamID and GameState:live,future,past of current season
    """

    path = 'schedule'
    query = {'season':season,'scheduleType':'game schedule'}
   
    if(teamId != None):
        query.update({'teamId':teamId})
    
    query.update(defaultParams)
    data = await getMlbData(statsBaseUrl+path, query)
    gameTypes = await getGameTypes()
    fullSchedule = formatScheduleData(data,gameTypes)
    
    if(gameState == None):
        return fullSchedule
    
    requiredSchedule = []
    
    for game in fullSchedule:
        if(game['statusCode'] in ['I','M','N'] and gameState == GameState.live):
            requiredSchedule.append(game)
        elif(game['statusCode'] in ['O','F'] and gameState == GameState.past):
            requiredSchedule.append(game)
        elif(game['statusCode'] in ['S','P'] and gameState == GameState.future):
            requiredSchedule.append(game)
    
    return requiredSchedule
