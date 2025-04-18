from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from db.connection import db_connect, close_db_connection
from passlib.context import CryptContext
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/player_management", tags=["Player_Management"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PlayerInviteRequest(BaseModel):
    coach_id: int
    player_name: str
    player_email: EmailStr
    team_id: int


def send_email(to_email, subject, content):
    load_dotenv()

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    msg.attach(MIMEText(content, "html"))

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

        cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'coach'", (data.coach_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Invalid coach ID.")

        cursor.execute("SELECT id FROM teams WHERE id = %s AND coach_id = %s", (data.team_id, data.coach_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Team does not exist or is not owned by this coach.")

        cursor.execute("SELECT id FROM users WHERE email = %s", (data.player_email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists.")

        random_password = secrets.token_urlsafe(8)
        hashed_password = pwd_context.hash(random_password)

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'player')
            RETURNING id
        """, (data.player_name, data.player_email, hashed_password))
        player_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO team_players (team_id, player_id)
            VALUES (%s, %s)
        """, (data.team_id, player_id))

        connection.commit()

        # Convert Google Drive share link to direct image link
        google_drive_view_link = "https://drive.google.com/file/d/15S04fRHnQzbQHAz9pL1VHv3CqkVDBDaO/view?usp=drive_link"
        file_id = google_drive_view_link.split("/d/")[1].split("/")[0]
        image_url = f"https://drive.google.com/uc?export=view&id={file_id}"

        subject = "Welcome to Sport-Analytics - Login Credentials"
        content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
              <div style="text-align: center;">
                <img src="{image_url}" alt="Sport Analytics Logo" style="max-width: 180px; margin-bottom: 20px;">
              </div>
              <h2 style="color: #2c3e50;">Welcome to Sport-Analytics, {data.player_name}!</h2>
              <p style="color: #555555; font-size: 15px;">
                You have been successfully added to your team by your coach. Below are your login credentials:
              </p>
              <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 15px;"><strong>Email:</strong> {data.player_email}</p>
                <p style="margin: 0; font-size: 15px;"><strong>Password:</strong> {random_password}</p>
              </div>
              <p style="color: #555555; font-size: 15px;">
                Please log in and remember to change your password after your first login to ensure your account remains secure.
              </p>
              <p style="color: #555555; font-size: 15px;">
                If you have any questions, feel free to reach out to your coach or the system admin.
              </p>
              <p style="color: #999999; font-size: 13px; text-align: center; margin-top: 30px;">
                &copy; 2025 Sport-Analytics. All rights reserved.
              </p>
            </div>
          </body>
        </html>
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
