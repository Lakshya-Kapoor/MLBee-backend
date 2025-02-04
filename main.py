from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import schedule, team, player, auth, standing, article
from utils import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(team.router, prefix="/teams")
app.include_router(auth.router, prefix="/auth")
app.include_router(player.router,prefix="/players")
app.include_router(schedule.router,prefix="/schedule")
app.include_router(standing.router,prefix="/standings")
app.include_router(article.router, prefix="/articles")
