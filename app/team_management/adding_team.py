from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection
from datetime import datetime

router = APIRouter(prefix="/team_management", tags=["Team Management"])

class TeamCreateRequest(BaseModel):
    name: str
    coach_id: int

@router.post("/add_team", summary="Coach adds a new team")
def add_team(data: TeamCreateRequest):
    connection = None
    cursor = None

    try:
        # Connect to DB
        connection = db_connect()
        cursor = connection.cursor()

        # Validate coach
        cursor.execute("SELECT role FROM users WHERE id = %s", (data.coach_id,))
        coach = cursor.fetchone()

        if not coach:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "CoachNotFound",
                    "message": f"No user found with ID {data.coach_id}."
                }
            )
        
        if coach[0] != "coach":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "InvalidRole",
                    "message": "The specified user is not authorized to create a team (not a coach)."
                }
            )

        # Check for duplicate team name
        cursor.execute("SELECT id FROM teams WHERE name = %s", (data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "DuplicateTeamName",
                    "message": f"A team with the name '{data.name}' already exists."
                }
            )

        # Insert the team
        cursor.execute(
            "INSERT INTO teams (name, coach_id, created_at) VALUES (%s, %s, %s)",
            (data.name, data.coach_id, datetime.utcnow())
        )
        connection.commit()

        return {
            "success": True,
            "message": "✅ Team successfully created.",
            "team": {
                "name": data.name,
                "coach_id": data.coach_id
            }
        }

    except HTTPException as http_err:
        raise http_err  # re-raise handled exceptions
    except Exception as e:
        print(f"❌ Internal Server Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while creating the team."
            }
        )
    finally:
        close_db_connection(cursor, connection)
