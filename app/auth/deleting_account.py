from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, constr
from db.connection import db_connect, close_db_connection
from passlib.context import CryptContext
import traceback

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

        # Check if user exists and fetch password + role
        cursor.execute("SELECT password_hash, role FROM users WHERE id = %s", (data.user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Coach not found.")

        password_hash, role = result

        if role.lower() != "coach":
            raise HTTPException(status_code=403, detail="User is not a coach.")

        if not pwd_context.verify(data.password, password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password.")

        # Delete user and confirm deletion
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id", (data.user_id,))
        deleted_user = cursor.fetchone()

        if not deleted_user:
            raise HTTPException(status_code=404, detail="Coach not found or already deleted.")

        connection.commit()

        return {
            "success": True,
            "message": f"✅ Coach with ID {data.user_id} has been successfully deleted."
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print("❌ Internal Server Error while deleting coach:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while deleting the coach: {str(e)}"
        )

    finally:
        close_db_connection(cursor, connection)
