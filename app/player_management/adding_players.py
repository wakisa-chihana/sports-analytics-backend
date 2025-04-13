from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from db.connection import db_connect, close_db_connection
from passlib.context import CryptContext
import secrets
import smtplib
from email.mime.text import MIMEText

router = APIRouter(prefix="/player_management", tags=["Player_Management"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PlayerInviteRequest(BaseModel):
    coach_id: int
    player_name: str
    player_email: EmailStr
    team_id: int

def send_email(to_email, subject, content):
    import os
    from dotenv import load_dotenv
    load_dotenv()

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


@router.post("/invite-player", summary="Coach invites player to register")
def invite_player(data: PlayerInviteRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Check if coach exists
        cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'coach'", (data.coach_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Invalid coach ID.")

        # Check if team exists and belongs to this coach
        cursor.execute("SELECT id FROM teams WHERE id = %s AND coach_id = %s", (data.team_id, data.coach_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Team does not exist or does not belong to this coach.")

        # Check if email is already taken
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.player_email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Generate password and hash
        random_password = secrets.token_urlsafe(8)
        hashed_password = pwd_context.hash(random_password)

        # Create user (player)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'player')
        """, (data.player_name, data.player_email, hashed_password))
        player_id = cursor.lastrowid

        # Add to team_players
        cursor.execute("""
            INSERT INTO team_players (team_id, player_id)
            VALUES (%s, %s)
        """, (data.team_id, player_id))

        connection.commit()

        # Email player
        subject = "Welcome to the Sport-Analytics - Login Credentials"
        content = f"""
Hello {data.player_name},

You have been added to your team by your coach.

Login Credentials:
Email: {data.player_email}
Password: {random_password}

Please log in and change your password after your first login.

Regards,
System Admin
        """
        send_email(data.player_email, subject, content)

        return {
            "success": True,
            "message": "✅ Player invited successfully and credentials sent via email."
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")

    finally:
        close_db_connection(cursor, connection)
