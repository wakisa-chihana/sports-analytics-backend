from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, constr
from db.connection import db_connect, close_db_connection
from passlib.context import CryptContext

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic model for coach deletion
class CoachDeleteRequest(BaseModel):
    user_id: int
    password: constr(min_length=8)  # type: ignore

@router.delete("/delete-coach", summary="Delete a coach account")
def delete_coach_account(data: CoachDeleteRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Fetch coach details by user_id
        cursor.execute("SELECT password_hash, role FROM users WHERE id = %s", (data.user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Coach not found.")

        password_hash, role = result

        # Ensure user is a coach
        if role != "coach":
            raise HTTPException(status_code=403, detail="User is not a coach.")

        # Verify password
        if not pwd_context.verify(data.password, password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password.")

        # Delete the user
        cursor.execute("DELETE FROM users WHERE id = %s", (data.user_id,))
        connection.commit()

        return {
            "success": True,
            "message": f"✅ Coach with ID {data.user_id} has been deleted."
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error deleting coach: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while deleting the coach.")

    finally:
        close_db_connection(cursor, connection)
