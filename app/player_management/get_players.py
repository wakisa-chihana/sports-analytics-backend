from fastapi import APIRouter, HTTPException
from db.connection import db_connect, close_db_connection
import psycopg2.extras

router = APIRouter(prefix="/team_players", tags=["Player_Management"])

@router.get("/team/{team_id}/coach/{coach_id}", summary="Get all players in a team for a coach")
def get_players_by_team_and_coach(team_id: int, coach_id: int):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # ✅ Verify the team belongs to the coach
        cursor.execute(
            "SELECT id FROM teams WHERE id = %s AND coach_id = %s",
            (team_id, coach_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Unauthorized access: This team does not belong to the specified coach.")

        # ✅ Retrieve all players in the team with profile and position
        query = """
            SELECT 
                u.id AS player_id,
                u.name AS player_name,
                u.email AS player_email,
                tp.position,
                pp.age, pp.height_cm, pp.weight_kgs,
                pp.preferred_foot_encoded, pp.weak_foot, pp.skill_moves,
                pp.crossing, pp.finishing, pp.heading_accuracy, pp.short_passing,
                pp.volleys, pp.dribbling, pp.curve, pp.freekick_accuracy,
                pp.long_passing, pp.ball_control, pp.acceleration, pp.sprint_speed,
                pp.agility, pp.reactions, pp.balance, pp.shot_power,
                pp.jumping, pp.stamina, pp.strength, pp.long_shots,
                pp.aggression, pp.interceptions, pp.positioning, pp.vision,
                pp.penalties, pp.composure, pp.marking, pp.standing_tackle,
                pp.sliding_tackle, pp.overall_performance
            FROM team_players tp
            JOIN users u ON tp.player_id = u.id
            LEFT JOIN player_profiles pp ON u.id = pp.player_id
            WHERE tp.team_id = %s
        """
        cursor.execute(query, (team_id,))
        players = cursor.fetchall()

        return {
            "success": True,
            "team_id": team_id,
            "coach_id": coach_id,
            "players": players
        }

    except psycopg2.Error as db_err:
        raise HTTPException(status_code=500, detail=f"PostgreSQL error: {db_err.pgerror}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)
