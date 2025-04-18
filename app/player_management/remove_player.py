from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os

from db.connection import close_db_connection, db_connect

# Load environment variables
load_dotenv()

# Pydantic model for remove player request
class RemovePlayerRequest(BaseModel):
    team_id: int
    player_id: int
    coach_id: int


# FastAPI app and router
app = FastAPI()
router = APIRouter(prefix="/team_players", tags=["Player_Management"])


@router.delete("/remove", summary="Remove a player from a team and associated data")
def remove_player_from_team(data: RemovePlayerRequest):
    connection = None
    cursor = None

    try:
        # Connect to the database
        connection = db_connect()
        cursor = connection.cursor()

        # ✅ Ensure the team belongs to the coach
        cursor.execute(
            "SELECT id FROM teams WHERE id = %s AND coach_id = %s",
            (data.team_id, data.coach_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Unauthorized: Coach does not own this team.")

        # ✅ Check if the player is part of the team
        cursor.execute(
            "SELECT id FROM team_players WHERE team_id = %s AND player_id = %s",
            (data.team_id, data.player_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Player not found in the team.")

        # ✅ Delete the player's associated data from multiple tables
        # Delete from player_profiles
        cursor.execute(
            "DELETE FROM player_profiles WHERE player_id = %s",
            (data.player_id,)
        )

        # Delete from notifications
        cursor.execute(
            "DELETE FROM notifications WHERE user_id = %s",
            (data.player_id,)
        )

        # Delete from password_reset_tokens
        cursor.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = %s",
            (data.player_id,)
        )

        # ✅ Delete the player from the team
        cursor.execute(
            "DELETE FROM team_players WHERE team_id = %s AND player_id = %s",
            (data.team_id, data.player_id)
        )
        connection.commit()

        return {
            "success": True,
            "message": f"Player (ID: {data.player_id}) and their associated data removed from team (ID: {data.team_id})."
        }

    except psycopg2.Error as db_err:
        raise HTTPException(status_code=500, detail=f"PostgreSQL error: {db_err.pgerror}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)


# Include the router in the FastAPI app
app.include_router(router)
