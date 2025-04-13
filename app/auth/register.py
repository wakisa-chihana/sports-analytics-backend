from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field, constr
from passlib.context import CryptContext
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
import secrets

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic model for user registration
class UserCreate(BaseModel):
    name: str = Field(..., example="wakisa Doe", description="Full name of the user")
    email: EmailStr = Field(..., example="wakisa@example.com", description="Valid email address")
    password: constr(min_length=8) = Field(  # type: ignore
        ..., example="securePass123", description="Password (min. 8 characters)"
    )
    role: constr(to_lower=True, pattern="^(coach|player)$") = Field(  # type: ignore
        ..., example="coach", description="Role of the user: 'coach' or 'player'"
    )

@router.post("/register", summary="Register a new user")
def register_user(user: UserCreate, response: Response):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Check if the email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered.")

        # Hash the password
        hashed_password = pwd_context.hash(user.password)

        # Insert the new user
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """,
            (user.name, user.email, hashed_password, user.role)
        )
        connection.commit()

        # Fetch the newly created user's ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        user_id = cursor.fetchone()[0]

        # Generate a session token
        session_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=3)

        response.set_cookie(
            key="122002",
            value=session_token,
            httponly=True,
            max_age=3 * 3600,
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"
        )

        return {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "message": "✅ User successfully registered and session started."
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error in register_user: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during registration.")

    finally:
        close_db_connection(cursor, connection)
