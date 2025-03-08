import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

msg = EmailMessage()
msg.set_content("This is a test email from Python.")
msg["Subject"] = "Test Email"
msg["From"] = EMAIL_USER
msg["To"] = "samuyeldammu6@gmail.com"  # Replace with your email

try:
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)
    server.quit()
    print("✅ Test email sent successfully!")
except Exception as e:
    print("❌ Error sending test email:", e)
