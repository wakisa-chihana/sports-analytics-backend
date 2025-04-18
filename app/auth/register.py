from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field, constr
from passlib.context import CryptContext
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "fallback-super-secret-key")
if SECRET_KEY == "fallback-super-secret-key":
    print("Warning: Using fallback secret key! Make sure to set COOKIE_SECRET_KEY in .env.")
serializer = URLSafeTimedSerializer(SECRET_KEY)

class UserCreate(BaseModel):
    name: str = Field(..., example="wakisa Doe", description="Full name of the user")
    email: EmailStr = Field(..., example="wakisa@example.com", description="Valid email address")
    password: constr(min_length=8) = Field(..., example="securePass123", description="Password (min. 8 characters)") # type: ignore
    role: constr(to_lower=True, pattern="^(coach|player)$") = Field(..., example="coach", description="Role of the user: 'coach' or 'player'") # type: ignore

@router.post("/register", summary="Register a new user")
def register_user(user: UserCreate, response: Response):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered.")

        hashed_password = pwd_context.hash(user.password)

        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (user.name, user.email, hashed_password, user.role)
        )
        connection.commit()

        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        user_id = cursor.fetchone()[0]

        user_data = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }

        cookie_value = serializer.dumps(user_data)

        expires = datetime.utcnow() + timedelta(hours=3)

        response.set_cookie(
            key="122002",
            value=cookie_value,
            httponly=True,
            secure=True,
            max_age=3 * 3600,
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"
        )

        return {"status": "ok", "message": "Registration successful"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error in register_user: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during registration. Please try again later.")

    finally:
        close_db_connection(cursor, connection)
