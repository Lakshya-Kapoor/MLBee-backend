from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import schedule, team, player, auth, standing, article
from utils import database
from fastapi.responses import RedirectResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def redirect_to_https(request: Request, call_next):
    if request.url.scheme == "http" or request.headers.get("X-Forwarded-Proto", "") == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url)
    response = await call_next(request)
    return response

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
