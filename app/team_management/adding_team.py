from fastapi import APIRouter, HTTPException, status
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
        # Connect to DB (Make sure your db_connect function is for PostgreSQL)
        connection = db_connect()
        cursor = connection.cursor()

        # Validate coach role
        cursor.execute("SELECT role FROM users WHERE id = %s", (data.coach_id,))
        coach = cursor.fetchone()

        if not coach:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with the specified coach ID."
            )
        
        if coach[0] != "coach":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The specified user is not authorized to create a team (not a coach)."
            )

        # Check for duplicate team name
        cursor.execute("SELECT id FROM teams WHERE name = %s", (data.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A team with the name '{data.name}' already exists."
            )

        # Insert the team
        cursor.execute(
            "INSERT INTO teams (name, coach_id, created_at) VALUES (%s, %s, %s) RETURNING id",
            (data.name, data.coach_id, datetime.utcnow())
        )
        team_id = cursor.fetchone()[0]  # Get the inserted team id

        # Commit the changes
        connection.commit()

        return {
            "success": True,
            "message": "✅ Team successfully created.",
            "team": {
                "id": team_id,
                "name": data.name,
                "coach_id": data.coach_id
            }
        }

    except HTTPException as http_err:
        raise http_err  # re-raise handled exceptions
    except Exception as e:
        print(f"❌ Internal Server Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the team."
        )
    finally:
        close_db_connection(cursor, connection)
