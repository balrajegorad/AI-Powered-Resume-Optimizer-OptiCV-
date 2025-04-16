import random
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(recipient_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"Your OTP code for signup is: {otp}")
    msg["Subject"] = "Your OTP for OptiCV"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def store_otp(email: str, otp: str):
    otp_store[email] = otp

def verify_otp(email: str, otp: str) -> bool:
    return otp_store.get(email) == otp
