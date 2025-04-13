from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection

router = APIRouter(prefix="/team_management", tags=["Team Management"])

class TeamUpdateRequest(BaseModel):
    team_id: int
    coach_id: int
    new_name: str

@router.put("/update", summary="Coach updates their team name")
def update_team(data: TeamUpdateRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Verify team and ownership
        cursor.execute("SELECT coach_id FROM teams WHERE id = %s", (data.team_id,))
        team = cursor.fetchone()
        if not team:
            raise HTTPException(status_code=404, detail={
                "error": "TeamNotFound",
                "message": "Team does not exist."
            })
        if team[0] != data.coach_id:
            raise HTTPException(status_code=403, detail={
                "error": "Unauthorized",
                "message": "You do not have permission to update this team."
            })

        # Check if name exists elsewhere
        cursor.execute("SELECT id FROM teams WHERE name = %s AND id != %s", (data.new_name, data.team_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail={
                "error": "DuplicateTeamName",
                "message": "Another team with this name already exists."
            })

        # Update team name
        cursor.execute("UPDATE teams SET name = %s WHERE id = %s", (data.new_name, data.team_id))
        connection.commit()

        return {"success": True, "message": f"✅ Team name updated to '{data.new_name}'."}

    except Exception as e:
        print(f"❌ Error updating team: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while updating the team."
        })
    finally:
        close_db_connection(cursor, connection)




