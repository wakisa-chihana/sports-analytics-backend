from fastapi import APIRouter, HTTPException, Query
from db.connection import db_connect, close_db_connection

router = APIRouter(prefix="/team_management", tags=["Team Management"])

@router.get("/get_coach_teams", summary="Get all teams belonging to a coach")
def get_coach_teams(coach_id: int = Query(..., description="ID of the coach")) -> dict:
    """
    Fetch all teams created by the specified coach.

    Query Parameters:
    - coach_id: The ID of the coach

    Returns:
    - A list of teams if found
    """
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Verify coach exists and is a coach
        cursor.execute("SELECT role FROM users WHERE id = %s", (coach_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail={
                "error": "CoachNotFound",
                "message": f"No user found with ID {coach_id}."
            })

        if user[0] != "coach":
            raise HTTPException(status_code=400, detail={
                "error": "InvalidRole",
                "message": "This user is not a coach."
            })

        # Fetch teams
        cursor.execute("SELECT id, name, created_at FROM teams WHERE coach_id = %s", (coach_id,))
        teams = cursor.fetchall()

        if not teams:
            return {
                "success": True,
                "message": "No teams found for this coach.",
                "teams": []
            }

        # Format results
        team_list = [
            {"id": team[0], "name": team[1], "created_at": team[2].strftime("%Y-%m-%d %H:%M:%S")}
            for team in teams
        ]

        return {
            "success": True,
            "message": f"{len(team_list)} team(s) found for coach ID {coach_id}.",
            "teams": team_list
        }

    except Exception as e:
        print(f"❌ Error retrieving teams for coach ID {coach_id}: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "InternalServerError",
            "message": "An error occurred while retrieving the teams."
        })

    finally:
        close_db_connection(cursor, connection)
