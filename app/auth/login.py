from fastapi import APIRouter, HTTPException, Response
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/users", tags=["Users"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cookie secret
SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "fallback-super-secret-key")
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Login model
class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="wakisa@example.com")
    password: str = Field(..., example="yourpassword123")

@router.post("/login", summary="Login user and start session")
def login_user(user: UserLogin, response: Response):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor(dictionary=True)

        # Fetch user by email
        cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = %s", (user.email,))
        user_record = cursor.fetchone()

        if not user_record:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Check password
        if not pwd_context.verify(user.password, user_record["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Prepare user data for cookie
        user_data = {
            "id": user_record["id"],
            "name": user_record["name"],
            "email": user_record["email"],
            "role": user_record["role"]
        }

        # Sign the cookie
        cookie_value = serializer.dumps(user_data)
        expires = datetime.utcnow() + timedelta(hours=3)

        # Set cookie
        response.set_cookie(
            key="user_session",
            value=cookie_value,
            httponly=True,
            secure=True,
            max_age=3 * 3600,
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"
        )

        return {"status": "ok", "message": "Login successful"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error in login_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login.")

    finally:
        close_db_connection(cursor, connection)
