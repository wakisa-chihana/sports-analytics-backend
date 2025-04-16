from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field, constr
from passlib.context import CryptContext
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
from dotenv import load_dotenv

# 🌍 Load .env variables
load_dotenv()

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Secret key for cookie signing (load from .env in production)
SECRET_KEY = os.getenv("COOKIE_SECRET_KEY", "fallback-super-secret-key")
if SECRET_KEY == "fallback-super-secret-key":
    print("Warning: Using fallback secret key! Make sure to set COOKIE_SECRET_KEY in .env.")
serializer = URLSafeTimedSerializer(SECRET_KEY)

class UserCreate(BaseModel):
    name: str = Field(..., example="wakisa Doe", description="Full name of the user")
    email: EmailStr = Field(..., example="wakisa@example.com", description="Valid email address")
    password: constr(min_length=8) = Field(..., example="securePass123", description="Password (min. 8 characters)")  # type: ignore
    role: constr(to_lower=True, pattern="^(coach|player)$") = Field(..., example="coach", description="Role of the user: 'coach' or 'player'")  # type: ignore

@router.post("/register", summary="Register a new user")
def register_user(user: UserCreate, response: Response):
    connection = None
    cursor = None

    try:
        # 🔄 Connect to DB
        connection = db_connect()
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered.")

        # Hash the password securely
        hashed_password = pwd_context.hash(user.password)

        # Insert new user into DB
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (user.name, user.email, hashed_password, user.role)
        )
        connection.commit()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        user_id = cursor.fetchone()[0]

        # 🍪 Data to store in secure cookie (minimal user info)
        user_data = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }

        # 🔐 Sign the user data securely
        cookie_value = serializer.dumps(user_data)

        # 🕒 Expire cookie after 3 hours
        expires = datetime.utcnow() + timedelta(hours=3)

        # Set the secure cookie
        response.set_cookie(
            key="122002",
            value=cookie_value,
            httponly=True,
            secure=True,  # Ensure True when using HTTPS in production
            max_age=3 * 3600,  # 3 hours expiration
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"  # Lax is a reasonable default for many scenarios
        )

        return {"status": "ok", "message": "Registration successful"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error in register_user: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during registration.")

    finally:
        close_db_connection(cursor, connection)

