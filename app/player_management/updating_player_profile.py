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

@router.put("/update_prifle", summary="Update an existing player profile")
def update_player_profile(data: PlayerProfileRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # ✅ Check if the player profile exists
        cursor.execute("SELECT id FROM player_profiles WHERE player_id = %s", (data.player_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Player profile not found.")

        # ✅ Update profile
        update_query = """
            UPDATE player_profiles SET
                age = %(age)s,
                height_cm = %(height_cm)s,
                weight_kgs = %(weight_kgs)s,
                preferred_foot_encoded = %(preferred_foot_encoded)s,
                weak_foot = %(weak_foot)s,
                skill_moves = %(skill_moves)s,
                crossing = %(crossing)s,
                finishing = %(finishing)s,
                heading_accuracy = %(heading_accuracy)s,
                short_passing = %(short_passing)s,
                volleys = %(volleys)s,
                dribbling = %(dribbling)s,
                curve = %(curve)s,
                freekick_accuracy = %(freekick_accuracy)s,
                long_passing = %(long_passing)s,
                ball_control = %(ball_control)s,
                acceleration = %(acceleration)s,
                sprint_speed = %(sprint_speed)s,
                agility = %(agility)s,
                reactions = %(reactions)s,
                balance = %(balance)s,
                shot_power = %(shot_power)s,
                jumping = %(jumping)s,
                stamina = %(stamina)s,
                strength = %(strength)s,
                long_shots = %(long_shots)s,
                aggression = %(aggression)s,
                interceptions = %(interceptions)s,
                positioning = %(positioning)s,
                vision = %(vision)s,
                penalties = %(penalties)s,
                composure = %(composure)s,
                marking = %(marking)s,
                standing_tackle = %(standing_tackle)s,
                sliding_tackle = %(sliding_tackle)s
            WHERE player_id = %(player_id)s
        """
        cursor.execute(update_query, data.dict())
        connection.commit()

        return {
            "success": True,
            "message": f"✅ Player profile for user ID {data.player_id} updated successfully."
        }

    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"MySQL error: {db_err.msg}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        close_db_connection(cursor, connection)
