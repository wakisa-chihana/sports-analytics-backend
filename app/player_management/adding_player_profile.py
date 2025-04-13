from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection
import mysql.connector

router = APIRouter(prefix="/player_profile", tags=["Player_Management"])

class PlayerProfileRequest(BaseModel):
    player_id: int
    age: int
    height_cm: float
    weight_kgs: float
    preferred_foot_encoded: int
    weak_foot: int
    skill_moves: int
    crossing: int
    finishing: int
    heading_accuracy: int
    short_passing: int
    volleys: int
    dribbling: int
    curve: int
    freekick_accuracy: int
    long_passing: int
    ball_control: int
    acceleration: int
    sprint_speed: int
    agility: int
    reactions: int
    balance: int
    shot_power: int
    jumping: int
    stamina: int
    strength: int
    long_shots: int
    aggression: int
    interceptions: int
    positioning: int
    vision: int
    penalties: int
    composure: int
    marking: int
    standing_tackle: int
    sliding_tackle: int

@router.post("/add", summary="Add a new player profile")
def add_player_profile(data: PlayerProfileRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # ✅ Check if the player exists and is of role 'player'
        cursor.execute(
            "SELECT id FROM users WHERE id = %s AND role = 'player'",
            (data.player_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Player not found or not assigned the 'player' role.")

        # ✅ Insert profile
        query = """
            INSERT INTO player_profiles (
                player_id, age, height_cm, weight_kgs, preferred_foot_encoded,
                weak_foot, skill_moves, crossing, finishing, heading_accuracy,
                short_passing, volleys, dribbling, curve, freekick_accuracy,
                long_passing, ball_control, acceleration, sprint_speed, agility,
                reactions, balance, shot_power, jumping, stamina, strength,
                long_shots, aggression, interceptions, positioning, vision,
                penalties, composure, marking, standing_tackle, sliding_tackle
            ) VALUES (
                %(player_id)s, %(age)s, %(height_cm)s, %(weight_kgs)s, %(preferred_foot_encoded)s,
                %(weak_foot)s, %(skill_moves)s, %(crossing)s, %(finishing)s, %(heading_accuracy)s,
                %(short_passing)s, %(volleys)s, %(dribbling)s, %(curve)s, %(freekick_accuracy)s,
                %(long_passing)s, %(ball_control)s, %(acceleration)s, %(sprint_speed)s, %(agility)s,
                %(reactions)s, %(balance)s, %(shot_power)s, %(jumping)s, %(stamina)s, %(strength)s,
                %(long_shots)s, %(aggression)s, %(interceptions)s, %(positioning)s, %(vision)s,
                %(penalties)s, %(composure)s, %(marking)s, %(standing_tackle)s, %(sliding_tackle)s
            )
        """
        cursor.execute(query, data.dict())
        connection.commit()

        return {
            "success": True,
            "message": f"✅ Player profile for user ID {data.player_id} added successfully."
        }

    except mysql.connector.IntegrityError as ie:
        # Unique or foreign key constraint violation
        raise HTTPException(status_code=400, detail=f"Database integrity error: {str(ie)}")

    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"MySQL error: {db_err.msg}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)
