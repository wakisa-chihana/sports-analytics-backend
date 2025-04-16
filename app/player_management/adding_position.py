from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection
import mysql.connector

router = APIRouter(prefix="/team_players", tags=["Player_Management"])

class UpdatePositionRequest(BaseModel):
    team_id: int
    player_id: int
    position: str

@router.put("/update-position", summary="Update a player's position in a team")
def update_player_position(data: UpdatePositionRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # ✅ Check if the player is assigned to the team
        cursor.execute(
            "SELECT id FROM team_players WHERE team_id = %s AND player_id = %s",
            (data.team_id, data.player_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Player is not assigned to this team.")

        # ✅ Update the position
        cursor.execute(
            "UPDATE team_players SET position = %s WHERE team_id = %s AND player_id = %s",
            (data.position, data.team_id, data.player_id)
        )
        connection.commit()

        return {
            "success": True,
            "message": f"✅ Position for player {data.player_id} in team {data.team_id} updated to '{data.position}'."
        }

    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"MySQL error: {db_err.msg}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)
