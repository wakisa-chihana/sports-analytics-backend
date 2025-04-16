from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr
from db.connection import db_connect, close_db_connection
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Request model for updating user info
class UserUpdateRequest(BaseModel):
    user_id: int
    old_password: constr(min_length=8) # type: ignore
    new_name: str | None = None
    new_email: EmailStr | None = None
    new_password: constr(min_length=8) | None = None # type: ignore

@router.patch("/update", summary="Update user information")
def update_user_info(data: UserUpdateRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Check if user exists and get current password
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (data.user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found.")
        
        current_hash = result[0]

        # Verify old password
        if not pwd_context.verify(data.old_password, current_hash):
            raise HTTPException(status_code=401, detail="Incorrect current password.")

        # Build update query dynamically
        update_fields = []
        update_values = []

        if data.new_name:
            update_fields.append("name = %s")
            update_values.append(data.new_name)

        if data.new_email:
            update_fields.append("email = %s")
            update_values.append(data.new_email)

        if data.new_password:
            hashed_new = pwd_context.hash(data.new_password)
            update_fields.append("password_hash = %s")
            update_values.append(hashed_new)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update.")

        update_values.append(data.user_id)

        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, tuple(update_values))
        connection.commit()

        return {"success": True, "message": "✅ User information updated successfully."}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while updating user information.")

    finally:
        close_db_connection(cursor, connection)
