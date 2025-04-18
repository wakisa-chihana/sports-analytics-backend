from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os

from db.connection import close_db_connection, db_connect

# Load environment variables
load_dotenv()

# Pydantic model for the request to remove player by email
class RemovePlayerByEmailRequest(BaseModel):
    email: str

# FastAPI app and router
app = FastAPI()
router = APIRouter(prefix="/team_players", tags=["Player_Management"])

@router.delete("/remove_by_email", summary="Remove a player based on their email and delete associated data")
def remove_player_by_email(data: RemovePlayerByEmailRequest):
    connection = None
    cursor = None

    try:
        # Connect to the database
        connection = db_connect()
        cursor = connection.cursor()

        # ✅ Verify the email exists in the users table
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (data.email,)
        )
        player = cursor.fetchone()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found with the provided email.")

        player_id = player[0]

        # ✅ Delete the player's associated data from multiple tables
        # Delete from player_profiles
        cursor.execute(
            "DELETE FROM player_profiles WHERE player_id = %s",
            (player_id,)
        )

        # Delete from notifications
        cursor.execute(
            "DELETE FROM notifications WHERE user_id = %s",
            (player_id,)
        )

        # Delete from password_reset_tokens
        cursor.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = %s",
            (player_id,)
        )

        # ✅ Delete the player from the team
        cursor.execute(
            "DELETE FROM team_players WHERE player_id = %s",
            (player_id,)
        )

        # ✅ Finally, delete the player from the users table
        cursor.execute(
            "DELETE FROM users WHERE id = %s",
            (player_id,)
        )

        # Commit the transaction
        connection.commit()

        return {
            "success": True,
            "message": f"Player with email {data.email} and their associated data removed."
        }

    except psycopg2.Error as db_err:
        raise HTTPException(status_code=500, detail=f"PostgreSQL error: {db_err.pgerror}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)

# Include the router in the FastAPI app
app.include_router(router)
