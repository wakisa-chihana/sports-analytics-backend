from flask import app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import deleting_account, login, password_reset, password_reset_request, register, update_user
from app.player_management import adding_player_profile, adding_players, adding_position, get_players, updating_player_profile
from app.team_management import adding_team, get_coach_teams, updating_team
from db.connection import get_db
from fastapi import Depends, HTTPException, status
from db.db_api import checkdb_connection
from app.team_management import deleting_team
from fastapi.responses import JSONResponse

app = FastAPI()

origins = [
    "http://localhost:3000",  # dev
    "https://your-frontend-domain.com",  # prod
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#status route to check if the API is running
@app.get("/", tags=["Root"])
def read_root():
    return {"status": "welcome to the sports analytics API"}

@app.get("/dbConnect", tags=["Database"])
def db_connect_route():
    return checkdb_connection()
   
#authentication routes
app.include_router(register.router)
app.include_router(login.router)
app.include_router(password_reset_request.router)
app.include_router(password_reset.router)
app.include_router(deleting_account.router)
app.include_router(update_user.router)

# team management routes
app.include_router(adding_team.router)
app.include_router(deleting_team.router)
app.include_router(get_coach_teams.router)
app.include_router(updating_team.router)


# player management routes
app.include_router(adding_players.router)
app.include_router(adding_player_profile.router)
app.include_router(updating_player_profile.router)
app.include_router(adding_position.router)
app.include_router(get_players.router)