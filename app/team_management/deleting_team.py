from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection

router = APIRouter(prefix="/team_management", tags=["Team Management"])

class TeamDeleteRequest(BaseModel):
    team_id: int
    coach_id: int
    team_name: str

@router.delete("/delete", summary="Coach deletes their team")
def delete_team(data: TeamDeleteRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Check if the team exists
        cursor.execute(
            "SELECT name, coach_id FROM teams WHERE id = %s",
            (data.team_id,)
        )
        team = cursor.fetchone()

        if not team:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "TeamNotFound",
                    "message": f"Team with ID {data.team_id} does not exist."
                }
            )

        db_team_name, db_coach_id = team

        # Check coach ownership
        if db_coach_id != data.coach_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "UnauthorizedAccess",
                    "message": "You are not authorized to delete this team."
                }
            )

        # Confirm name matches
        if db_team_name.strip().lower() != data.team_name.strip().lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "TeamNameMismatch",
                    "message": f"Provided team name '{data.team_name}' does not match actual name '{db_team_name}'."
                }
            )

        # Perform deletion
        cursor.execute("DELETE FROM teams WHERE id = %s", (data.team_id,))
        connection.commit()

        return {
            "success": True,
            "message": f"✅ Team '{db_team_name}' (ID {data.team_id}) deleted successfully."
        }

    except HTTPException:
        raise  # Propagate known HTTP errors

    except Exception as e:
        print(f"❌ Error deleting team: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while deleting the team."
            }
        )
    finally:
        close_db_connection(cursor, connection)
