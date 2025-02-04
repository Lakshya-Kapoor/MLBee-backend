from utils.config import NEWS_API_KEY,GEMINI_API_KEY
from jobs.update_articles.gemini_req_wrapper import gemini_api_call
from httpx import AsyncClient 
from enum import Enum
from models.article import Article
import google.generativeai as genai
import typing_extensions as typing 
import json
import dateutil.parser
class SearchIn(Enum):
    title = "title"
    description = "description"
    content = "content"

class SortBy(Enum):
    popularity = "popularity"
    relevancy = "relevancy"
    publishedAt = "publishedAt"

class Option(Enum):
    everything = "everything"
    topheadlines = "top-headlines"
    source = "top-headlines/sources"
class ArticleResponseSchema(typing.TypedDict):
    title:str
    catchyPhrase:str
    description:str
    content:str
    tags:list[str]
class NewsApiDayLimit(Exception):
    def __init__(self):
        super().__init__("NewsApi daily limit reached")
class ArticleFormatError(Exception):
    def __init__(self):
        super().__init__("Article returned from model is not in correct format ")
class WriterModel:
    def __init__(self,model_to_use):
        self.model_instruction = "mimick the tone of a article writer for fans expressing him/her  opinion and facts"
        
        self.genration_config = genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=ArticleResponseSchema,
        temperature=0.7) 

        self.model_used = model_to_use

        self.model = genai.GenerativeModel(
            model_name=self.model_used,
            generation_config=self.genration_config,
            system_instruction=self.model_instruction)
        self.misc_tags = ["trade","rumour","history","prospects","recap","meme","stats","spring training","post season","world series","funny"]
    
    async def generate(self,url:str,feature:str) -> ArticleResponseSchema:
        
        prompt = f"""
        context: you are a article writer who writes about Major League Baseball
        task: Step1- read the article with the url provided here - {url},step2-generate an article for the mlb fans to read and engage featuring the {feature}
        step3 specify the tags for  the article from the given list of tags below
        Dont dos:  You should never mention the provided article in your article in any form, dont exaggerate the article lines keep it more close to article, 
        dos: step 1 divide the main content into paragraphs ,step 2 give subheading to these paragraphs
        tags:{self.misc_tags},add tag with player name that is revelant to the article, add tag with team name that is revalnt to the article 
        """
        response = await gemini_api_call(model=self.model,prompt=prompt)
        articleText = json.loads(response.text)
        return articleText

class NewsApiArticleGetter:
    def __init__(self):
        self.client = AsyncClient()
        self.model_to_use = "gemini-1.5-flash"
        genai.configure(api_key=GEMINI_API_KEY)
        self.writerModel = WriterModel(self.model_to_use)
        self.newsApi_day_limit = 1000
        self.newsApi_api_calls = 0
        self.max_retries_on_foramting_articles = 3

    async def get_articles_newsApi(self,q:str,option:Option = Option.everything,searchin:SearchIn|None = None,beg:str|None = None,sortBy:SortBy|None=None,pageSize:int|None = None,page:int|None = None):
        
        if(self.newsApi_api_calls > self.newsApi_day_limit):
            raise NewsApiDayLimit
        
        newsApiUrl = f"https://newsapi.org/v2/{option.value}"
        # language selected in english for the articles 
        params = {'q':q,'apiKey':NEWS_API_KEY,'language':"en"}
        if(searchin) : params['searchin'] = searchin.value
        if(beg) : params['beg'] = beg
        if(sortBy) : params['sortBy'] = sortBy.value
        if(pageSize) : params['pageSize'] = pageSize
        if(page) : params['page'] = page


        response = await self.client.get(newsApiUrl,params=params)
        self.newsApi_api_calls+=1
        
        if(response.status_code != 200):
            print(response)
            raise Exception("couldnt fetch data from newsapi")

        return response.json()
    async def filter_out_articles(self,articles:list,returnCount:int,featuring:str) -> list[int]:
    
        articleString = {i:{"description":article['description'],"url":article["url"]} for i,article in enumerate(articles)}

        systemInstruction = "be a article selector "
        generationConfig = genai.GenerationConfig(response_schema=list[int],temperature=0.0,response_mime_type="application/json")
        model = genai.GenerativeModel(model_name= self.model_to_use,system_instruction=systemInstruction,generation_config=generationConfig)
        prompt = f"""
        context: you are provided with some articles featuring {featuring} and you need to select {returnCount} number of articles based on the criteria
        Task: step 1 read the criteria step 2 read the articles(featuring {featuring}) description  provided below step 3 based on the criteria filter out {returnCount} number of articles 
        step4  output the list of serial numbers of selected articles
        criteria: 1.  article should have unique topic among other articles 2. article should be more revelant and interesting than others 
        articles:{articleString}"""

        response = await gemini_api_call(model=model,prompt=prompt)
        selectedList = json.loads(response.text)
        return selectedList[:returnCount]
    
    def format_into_article(self,articleText:ArticleResponseSchema,newsApiArticle)-> Article:
        try:
            return Article(
                    tags= articleText['tags'],
                    title= articleText['title'],
                    description=articleText['description'],
                    catchyPhrase= articleText['catchyPhrase'],
                    content=articleText['content'],
                    url =newsApiArticle['url'],
                    author= newsApiArticle['author'],
                    publishedDate= dateutil.parser.parse(newsApiArticle['publishedAt'])
            )
        except Exception:
            raise ArticleFormatError

    async def get_articles_players(self,playerName:str,beg:str|None = None,resultsCount:int = 1) -> list[Article]:

        query = f"+{playerName}" 
        articles = [] 
        fetchCount = min(resultsCount*5,20)
        newsApiResponse = await self.get_articles_newsApi(
            q=query,
            searchin=SearchIn.description,
            pageSize=fetchCount,
            beg=beg,
            sortBy=SortBy.popularity)

        if(newsApiResponse['totalResults'] == 0):
            return []
        
        selectedArticles = await self.filter_out_articles(
            newsApiResponse['articles'],
            min(len(newsApiResponse['articles']),resultsCount),
            featuring=playerName)
        for i in selectedArticles:
            tries = 0
            success = False
            while((not success) and tries<self.max_retries_on_foramting_articles):
                try:
                    articleText = await self.writerModel.generate(url = newsApiResponse['articles'][i]['url'],feature=playerName)
                    article = self.format_into_article(articleText=articleText,newsApiArticle=newsApiResponse['articles'][i])
                    success = True
                except ArticleFormatError:
                    tries+=1
            articles.append(article)

        return articles
    async def get_articles_mlb(self,beg:str|None = None,resultsCount:int=10):
        articles = []
        query = f"mlb OR Major League Baseball"
        fetchCount = min(resultsCount*3,60)

        newsApiResponse = await self.get_articles_newsApi(
            q=query,
            searchin=SearchIn.description,
            pageSize=resultsCount,
            beg=beg,
            sortBy=SortBy.popularity)

        if(newsApiResponse['totalResults'] == 0):
            return []

        selectedArticles = await self.filter_out_articles(
            newsApiResponse['articles'],
            min(len(newsApiResponse['articles']),resultsCount),
            featuring="Major League Baseball")
        # print(selectedArticles)
        for i in selectedArticles:
            tries = 0
            success = False
            while((not success) and tries<self.max_retries_on_foramting_articles):
                try:
                    articleText = await self.writerModel.generate(url = newsApiResponse['articles'][i]['url'],feature="Major League Baseball")
                    article = self.format_into_article(articleText=articleText,newsApiArticle=newsApiResponse['articles'][i])
                    success = True
                except ArticleFormatError:
                    tries+=1
            articles.append(article)

        return articles
    async def get_articles_team(self,teamName:str,beg:str|None = None,resultsCount:int =3) -> list[Article]:
        articles = []
        query = f"+{teamName}"
        fetchCount = min(resultsCount*5,30)
        newsApiResponse = await self.get_articles_newsApi(
            q=query,
            searchin=SearchIn.description,
            pageSize=fetchCount,
            beg=beg,
            sortBy=SortBy.popularity)
    
        if(newsApiResponse['totalResults'] == 0):
            return []
    
        selectedArticles = await self.filter_out_articles(
            newsApiResponse['articles'],
            min(len(newsApiResponse['articles']),resultsCount),
            featuring=teamName)
        for i in selectedArticles:
            tries = 0
            success = False
            while((not success ) and tries<self.max_retries_on_foramting_articles):
                try:
                    articleText = await self.writerModel.generate(url = newsApiResponse['articles'][i]['url'],feature=teamName)
                    article = self.format_into_article(articleText=articleText,newsApiArticle=newsApiResponse['articles'][i])
                    success = True
                except ArticleFormatError:
                    tries+=1
            articles.append(article)
    
        return articles
    
    async def  close(self):
        await self.client.aclose()
    