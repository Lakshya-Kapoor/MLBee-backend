from utils.database import init_db
from jobs.update_articles.newsApi_article_getter import NewsApiArticleGetter,NewsApiDayLimit
import asyncio
from models.article import Article
from models.player import Player
from models.team import Team
from models.progress import Progress,State
from jobs.update_articles.gemini_req_wrapper  import GeminiDayLimit
from datetime import datetime,timezone,timedelta
async def test():
    articleGetter  = NewsApiArticleGetter() 
    data = await articleGetter.get_articles_players("Juan Soto",resultsCount=1)
    for article in data:
        print(article)
    await articleGetter.close()

async def store_player_articles():
    global progress
    players = await Player.find().to_list()
    player_names = [player.name for player in players]
    while(progress.players_with_article_stored < len(player_names)):
        max_retries = 5
        tries = 0
        success = False
        while( (not success) and tries<max_retries):
            player_name = player_names[progress.players_with_article_stored]
            try:
                articles = await articleGetter.get_articles_players(playerName=player_name,resultsCount=2,beg=progress.last_complete_fetch_date)
                await Article.insert_many(articles)
                success = True
            except GeminiDayLimit as e:
                raise e
            except NewsApiDayLimit as e:
                raise e
            except Exception:
                tries+=1
        print(progress.players_with_article_stored)
        progress.players_with_article_stored+=1

async def store_team_articles():
    global progress
    teams = await Team.find().to_list()
    team_names = [team.name for team in teams]
    while(progress.teams_with_article_stored < len(team_names)):
        max_retries = 5
        tries = 0
        success = False
        while((not success) and tries<max_retries):
            
            team_name = team_names[progress.teams_with_article_stored]
            try:    
                articles = await articleGetter.get_articles_team(teamName=team_name,resultsCount=5,beg=progress.last_complete_fetch_date)
                await Article.insert_many(articles)
                success = True
            except GeminiDayLimit as e:
                raise e
            except NewsApiDayLimit as e:
                raise e
            except Exception:
                tries+=1   
        print(progress.teams_with_article_stored)
        progress.teams_with_article_stored+=1

async def store_mlb_articles():
    global progress
    max_retries = 5
    tries = 0  
    success = False  
    while((not success) and tries<max_retries):  
        try:
            articles = await articleGetter.get_articles_mlb(resultsCount=15,beg=progress.last_complete_fetch_date) 
            await Article.insert_many(articles)   
            success = True
           
        except GeminiDayLimit as e:
            raise e
        except NewsApiDayLimit as e:
            raise e
        except Exception:
            tries+=1    
    
        progress.mlb_articles_stored+=1
    print("done")

async def intialize_progess():
    global progress
    progress = await Progress.find_one({})
    if(progress.state == State.start):
        progress.players_with_article_stored = 0
        progress.teams_with_article_stored = 0
        progress.mlb_articles_stored = 0
        progress.last_execution_start_date = datetime.now(timezone.utc)
        progress.state = State.working

async def save_progress():
    global progress
    progress.last_executed_date = datetime.now(timezone.utc)
    await progress.save()
async def  main_func():
    await init_db()
    await intialize_progess()
    global articleGetter
    articleGetter = NewsApiArticleGetter()
    try:
        await store_player_articles()
        await store_team_articles()
        await store_mlb_articles()
        progress.last_complete_fetch_date = progress.last_execution_start_date - timedelta(days=1) # newsApi have a 24 hour delay
        progress.state = State.start
    except GeminiDayLimit:
        pass
    except NewsApiDayLimit:
        pass
    await articleGetter.close()
    del articleGetter
    await save_progress()
    # await test()
asyncio.run(main_func())