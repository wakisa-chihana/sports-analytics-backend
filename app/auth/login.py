from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from db.connection import db_connect, close_db_connection
from itsdangerous import URLSafeTimedSerializer
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

router = APIRouter(
    prefix="/Users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "fallback-super-secret-key")
serializer = URLSafeTimedSerializer(SECRET_KEY)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/login", summary="Log in a user")
def login_user(user: UserLogin, response: Response):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        cursor.execute("SELECT id, name, password_hash, role FROM users WHERE email = %s AND is_active = TRUE", (user.email,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id, name, password_hash, role = result

        if not pwd_context.verify(user.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_data = {
            "id": user_id,
            "name": name,
            "email": user.email,
            "role": role
        }

        cookie_value = serializer.dumps(user_data)

        # Expire the cookie after 3 hours
        expires = datetime.utcnow() + timedelta(hours=3)

        response.set_cookie(
            key="122002",
            value=cookie_value,
            httponly=True,
            secure=True,
            max_age=3 * 3600,  # 3 hours in seconds
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),  # Expiration time in GMT
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
