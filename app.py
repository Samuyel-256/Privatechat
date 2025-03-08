from flask import Flask, render_template, request, redirect, session, flash, url_for
import pandas as pd
import csv
import random
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # Secure session key

# CSV Files
USER_CSV = "users.csv"
CHAT_CSV = "chat_rooms.csv"

# 📌 Ensure CSV files exist with headers
def ensure_csv(filename, headers):
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

ensure_csv(USER_CSV, ["Name", "Email", "Password"])
ensure_csv(CHAT_CSV, ["Code", "Owner"])

# 📧 Function to Send OTP via Email
def send_otp(email):
    otp = str(random.randint(100000, 999999))
    session["otp"] = otp
    print(f"🔢 Generated OTP: {otp}")  # Debugging

    msg = EmailMessage()
    msg.set_content(f"Your OTP for Private Chat is: {otp}")
    msg["Subject"] = "Private Chat OTP Verification"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        server.send_message(msg)
        server.quit()
        print(f"✅ OTP sent to {email}")
    except Exception as e:
        print("❌ Error sending email:", e)
        flash("Failed to send OTP. Try again later.", "danger")

# 🏠 Home Page
@app.route("/")
def index():
    return render_template("index.html")

# 📝 Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        try:
            users_df = pd.read_csv(USER_CSV)
            users_df.columns = users_df.columns.str.strip()

            if "Email" not in users_df.columns:
                flash("CSV file is corrupted!", "danger")
                return redirect("/signup")

            if email in users_df["Email"].values:
                flash("Email already registered! Please log in.", "danger")
                return redirect("/signup")

            send_otp(email)
            session["temp_user"] = {"name": name, "email": email, "password": generate_password_hash(password)}
            return redirect("/verify-otp")

        except Exception as e:
            flash("Error processing signup!", "danger")
            print("❌ Signup error:", e)

    return render_template("signup.html")

# 🔢 OTP Verification
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "temp_user" not in session:
        flash("Session expired! Try signing up again.", "danger")
        return redirect("/signup")

    if request.method == "POST":
        entered_otp = request.form["otp"].strip()

        if entered_otp == session.get("otp"):
            user = session["temp_user"]
            with open(USER_CSV, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([user["name"], user["email"], user["password"]])

            session.pop("otp", None)
            session.pop("temp_user", None)
            flash("Signup successful! Please log in.", "success")
            return redirect("/login")
        else:
            flash("Invalid OTP! Try again.", "danger")

    return render_template("otp_verification.html")

# 🔑 Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        try:
            users_df = pd.read_csv(USER_CSV)
            users_df.columns = users_df.columns.str.strip()

            if "Email" not in users_df.columns or "Password" not in users_df.columns:
                flash("CSV file format error!", "danger")
                return redirect("/login")

            user = users_df[users_df["Email"] == email]

            if not user.empty and check_password_hash(user.iloc[0]["Password"], password):
                session["user"] = email
                flash("Login Successful!", "success")
                return redirect("/dashboard")
            else:
                flash("Invalid Email or Password!", "danger")

        except pd.errors.EmptyDataError:
            flash("No users found! Please Sign Up.", "danger")
        except Exception as e:
            flash("Login Error!", "danger")
            print("❌ Error:", e)

    return render_template("login.html")

# 🏠 Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please Login First!", "danger")
        return redirect("/login")
    return render_template("dashboard.html")

# 🔑 Generate Unique Chat Room Code
@app.route("/generate_code")
def generate_code():
    if "user" not in session:
        flash("Please Login First!", "danger")
        return redirect("/login")

    code = str(random.randint(100000, 999999))
    with open(CHAT_CSV, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([code, session["user"]])

    flash(f"Your Chat Room Code: {code}", "info")
    return redirect("/dashboard")

# 🔗 Join Chat Room
@app.route("/join_chat", methods=["POST"])
def join_chat():
    if "user" not in session:
        flash("Please Login First!", "danger")
        return redirect("/login")

    code = request.form["chat_code"].strip()
    try:
        chat_rooms = pd.read_csv(CHAT_CSV)

        if code in chat_rooms["Code"].values:
            return redirect(url_for("chat", code=code))
        else:
            flash("Invalid Chat Code!", "danger")

    except pd.errors.EmptyDataError:
        flash("No Chat Rooms Available!", "danger")

    return redirect("/dashboard")

# 💬 Chat Room
@app.route("/chat/<code>")
def chat(code):
    if "user" not in session:
        flash("Please Login First!", "danger")
        return redirect("/login")
    return render_template("chat.html", code=code)

# 🚪 Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect("/")

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
