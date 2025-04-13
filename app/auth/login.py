from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, constr
from passlib.context import CryptContext
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
import secrets

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="john@example.com", description="Registered email address")
    password: constr(min_length=8) = Field(..., example="securePass123", description="User's password ")  # type: ignore

@router.post("/login", summary="Login user and start session")
def login_user(user: UserLogin, response: Response):
    connection = None
    cursor = None

    try:
        # 🔄 Establish DB connection
        connection = db_connect()
        cursor = connection.cursor(dictionary=True)

        # 🔍 Check for user by email
        cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = %s", (user.email,))
        user_record = cursor.fetchone()

        if not user_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        # 🔐 Verify password
        if not pwd_context.verify(user.password, user_record["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        # 🍪 Generate session token and set cookie
        session_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=3)

        response.set_cookie(
            key="122002",  # Suggest changing to "session_token"
            value=session_token,
            httponly=True,
            max_age=3 * 3600,
            expires=expires.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            samesite="Lax"
        )

        return {
            "id": user_record["id"],
            "name": user_record["name"],
            "email": user_record["email"],
            "role": user_record["role"],
            "message": "✅ Login successful. Session started."
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error in login_user: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during login.")

    finally:
        close_db_connection(cursor, connection)
