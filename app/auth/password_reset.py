from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from db.connection import db_connect, close_db_connection
from datetime import datetime
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the router for the users endpoint
router = APIRouter(prefix="/users", tags=["Users"])

# Passlib context for consistent password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic model to handle password reset requests
class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password", summary="Reset user password")
def reset_password(data: PasswordResetRequest):
    connection = None
    cursor = None

    try:
        # Connect to the database
        connection = db_connect()
        cursor = connection.cursor()

        # Verify token existence and validity
        cursor.execute("""
            SELECT user_id, expires_at 
            FROM password_reset_tokens 
            WHERE token = %s AND is_used = FALSE
        """, (data.token,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")

        user_id, expires_at = result

        # Check for token expiration
        if expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired.")

        # Hash the new password using passlib for consistency
        hashed_password = pwd_context.hash(data.new_password)

        # Update password in database
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE id = %s
        """, (hashed_password, user_id))

        # Mark the token as used
        cursor.execute("""
            UPDATE password_reset_tokens 
            SET is_used = TRUE 
            WHERE token = %s
        """, (data.token,))

        # Commit changes
        connection.commit()

        return {"message": "✅ Password successfully reset."}

    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while resetting the password.")
    
    finally:
        close_db_connection(cursor, connection)
