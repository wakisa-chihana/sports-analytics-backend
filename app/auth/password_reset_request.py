from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from db.connection import db_connect, close_db_connection
from datetime import datetime, timedelta
import secrets
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

router = APIRouter(prefix="/users", tags=["Users"])

class PasswordResetRequest(BaseModel):
    email: EmailStr

@router.post("/request-password-reset", summary="Request a password reset email")
def request_password_reset(data: PasswordResetRequest):
    connection = None
    cursor = None

    try:
        connection = db_connect()
        cursor = connection.cursor()

        # Get user ID and name by email
        cursor.execute("SELECT id, name FROM users WHERE email = %s", (data.email,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Email not found.")
        
        user_id, name = result

        # Generate token and expiration
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        # Store token
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token, expires_at)
        )
        connection.commit()

        # Send email
        send_reset_email(data.email, token, name)

        return {"message": "✅ Password reset link sent to your email."}

    except Exception as e:
        print(f"❌ Error in request_password_reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while sending the reset email: {str(e)}")
    
    finally:
        close_db_connection(cursor, connection)

def send_reset_email(email: str, token: str, name: str):
    base_url = os.getenv("FRONTEND_RESET_URL")
    reset_link = f"{base_url}?token={token}"

    message = EmailMessage()
    message["Subject"] = "Password Reset Request"
    message["From"] = os.getenv("EMAIL_USER")
    message["To"] = email

    # HTML Email Content with Logo placed at the top
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://drive.google.com/uc?id=15S04fRHnQzbQHAz9pL1VHv3CqkVDBDaO" alt="Sports Analytics Logo" style="max-width: 200px; vertical-align: middle;">
            </div>
            <h2 style="color: #333333; text-align: center;">Password Reset Request</h2>
            <p style="color: #555555; font-size: 16px;">Hello, {name}</p>
            <p style="color: #555555; font-size: 16px;">A password reset was requested for your account in Sports Analytics. If this was not you, you can safely ignore this email.</p>
            <p style="color: #555555; font-size: 16px;">Click the button below to reset your password:</p>
            <div style="text-align: center;">
                <a href="{reset_link}" style="background-color: #031e37; color: white; padding: 15px 30px; font-size: 16px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #555555; font-size: 16px; text-align: center; margin-top: 20px;">This link will expire in 30 minutes.</p>
            <p style="color: #555555; font-size: 16px; text-align: center;">If you did not request a password reset, you can safely ignore this message.</p>
            <hr style="border: 1px solid #eeeeee; margin-top: 40px;">
            <p style="color: #777777; font-size: 14px; text-align: center;">&copy; {datetime.utcnow().year} Sports Analytics. All rights reserved.</p>
        </div>
    </body>
    </html>
    """

    # Plain text version of the email
    plain_text_content = f"""
    Password Reset Request

    Hello, {name}

    A password reset was requested for your account in Sports Analytics. If this was not you, you can safely ignore this email.

    Click the link below to reset your password:
    {reset_link}

    This link will expire in 30 minutes.

    If you did not request a password reset, you can safely ignore this message.

    © {datetime.utcnow().year} Sports Analytics. All rights reserved.
    """

    # Setting the email as multipart/alternative and adding plain text and HTML parts
    message.set_content(plain_text_content)  # Plain text part
    message.add_alternative(html_content, subtype="html")  # HTML part

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(message)
        print(f"✅ Reset email sent to {email}")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error while sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send password reset email: {e}")
    except Exception as e:
        print(f"❌ General error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while sending the email: {e}")
