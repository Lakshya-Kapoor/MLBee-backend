from beanie import Document
from datetime import datetime,timezone
from pydantic import Field
from pydantic import BaseModel
from enum import Enum
class Reactions(BaseModel):
    upVotes:int = Field(default=0)
    downVotes:int = Field(default=0)

class ReactionTypes(Enum):
    upVotes = "upVotes"
    downVotes = "downVotes"

class Article(Document):
    
    title:str|None
    catchyPhrase:str|None
    description:str|None
    content:str|None
    tags:list[str]|None
    author:str|None
    url:str|None
    publishedDate:datetime|None
    uploadDate:datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    reactions:Reactions = Field(default_factory=lambda: Reactions())
    class Settings:
        name = "articles"
