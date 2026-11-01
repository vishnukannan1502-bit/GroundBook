from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from datetime import date
import os
import smtplib
from email.message import EmailMessage

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "groundbook.db"
app = Flask(__name__)
def send_email(to_email, subject, body):
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_password:
        app.logger.error("Gmail credentials are missing.")
        return False

    message = EmailMessage()
    message["From"] = gmail_address
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_address, gmail_password)
            smtp.send_message(message)

        return True

    except Exception:
        app.logger.exception("Email sending failed.")
        return False
    app.secret_key = os.environ.get(
      "SECRET_KEY",
      "local-development-only-key"
)


GROUND_SEED_DATA = [
    # Existing Chennai venues
    (1, "Urban Football Arena", "Football", "Adyar, Chennai", 1000, 4.9, "Private"),
    (2, "Boundary Cricket Club", "Cricket", "Tambaram, Chennai", 800, 4.8, "Private"),
    (3, "Smash Point Courts", "Badminton", "Velachery, Chennai", 400, 4.7, "Private"),
    (4, "Hoops Park", "Basketball", "OMR, Chennai", 600, 4.6, "Private"),

    # Puducherry private venues
    (5, "City 5", "Football", "Krishna Nagar, Puducherry", 700, 5.0, "Private"),
    (6, "Matchbox Multi Sports Arena", "Cricket", "Puducherry", 800, 4.5, "Private"),
    (7, "Citizen Badminton Academy", "Badminton", "Thattanchavady, Puducherry", 400, 5.0, "Private"),
    (8, "Venkateswara Badminton Coaching Centre", "Badminton", "Villianur, Puducherry", 350, 4.7, "Private"),

    # Government sports facilities
    (9, "Indira Gandhi Sports Complex", "Football", "Uppalam, Puducherry", 600, 4.2, "Government"),
    (10, "Rajiv Gandhi Indoor Stadium", "Badminton", "Uppalam, Puducherry", 500, 4.0, "Government"),

    # College / university facilities
    (11, "Pondicherry University Sports Ground", "Cricket", "Kalapet, Puducherry", 500, 4.0, "College"),
    (12, "Tagore Arts College Ground", "Football", "Lawspet, Puducherry", 400, 4.0, "College"),
]
ALLOWED_TIME_SLOTS = {
    "06:00 AM – 07:00 AM",
    "07:00 AM – 08:00 AM",
    "08:00 AM – 09:00 AM",
    "05:00 PM – 06:00 PM",
    "06:00 PM – 07:00 PM",
    "07:00 PM – 08:00 PM",
}


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS grounds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                sport TEXT NOT NULL,
                location TEXT NOT NULL,
                price_per_hour INTEGER NOT NULL,
                rating REAL NOT NULL,
                venue_type TEXT NOT NULL DEFAULT 'Private'
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT NOT NULL COLLATE NOCASE UNIQUE,
               password_hash TEXT NOT NULL,
               created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
""")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ground_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ground_id) REFERENCES grounds(id),
                UNIQUE (ground_id, booking_date, time_slot)
            )
        """)
        try:
            connection.execute("""
                ALTER TABLE grounds
                ADD COLUMN venue_type TEXT NOT NULL DEFAULT 'Private'
            """)
        except sqlite3.OperationalError:
            pass

        connection.executemany("""
            INSERT OR IGNORE INTO grounds
            (id, name, sport, location, price_per_hour, rating,venue_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, GROUND_SEED_DATA)

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db() as connection:
            connection.execute("""
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            """, (name, email, password_hash))

        email_sent = send_email(
            email,
            "Welcome to GroundBook!",
            f"""
Hello {name},

Welcome to GroundBook!

Your account has been successfully created.

You can now log in and book your favourite sports grounds.

Thank you for joining us!

Team GroundBook
"""
        )

        return jsonify({
            "message": "Registration successful.",
            "email_sent": email_sent
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "This email is already registered."
        }), 409


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    with get_db() as connection:
        user = connection.execute("""
            SELECT id, name, email, password_hash
            FROM users WHERE email = ?
        """, (email,)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return jsonify({
        "message": "Login successful.",
        "name": user["name"]
    }), 200


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200


@app.get("/api/session")
def session_status():
    if "user_id" not in session:
        return jsonify({"logged_in": False}), 200

    return jsonify({
        "logged_in": True,
        "name": session.get("user_name")
    }), 200


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "GroundBook backend is running"
    })


@app.get("/api/grounds")
def list_grounds():
    with get_db() as connection:
        rows = connection.execute("""
            SELECT id, name, sport, location, price_per_hour, rating
            FROM grounds ORDER BY id
        """).fetchall()

    return jsonify([dict(row) for row in rows])


@app.post("/api/bookings")
def create_booking():
    if "user_id" not in session:
        return jsonify({"error": "Please log in to book a ground."}), 401

    data = request.get_json(silent=True) or {}

    ground_id = data.get("ground_id")
    customer_name = session.get("user_name", "")
    booking_date = str(data.get("booking_date", "")).strip()
    time_slot = str(data.get("time_slot", "")).strip()

    if not isinstance(ground_id, int) or isinstance(ground_id, bool):
        return jsonify({"error": "Please select a valid ground."}), 400

    if not customer_name or len(customer_name) > 80:
        return jsonify({
            "error": "Enter your name (maximum 80 characters)."
        }), 400

    try:
        selected_date = date.fromisoformat(booking_date)
    except ValueError:
        return jsonify({"error": "Choose a valid booking date."}), 400

    if selected_date < date.today():
        return jsonify({"error": "You cannot book a date in the past."}), 400

    if time_slot not in ALLOWED_TIME_SLOTS:
        return jsonify({
            "error": "Choose one of the available time slots."
        }), 400

    with get_db() as connection:
        ground = connection.execute("""
            SELECT id, name, location, price_per_hour
            FROM grounds WHERE id = ?
        """, (ground_id,)).fetchone()

        if ground is None:
            return jsonify({
                "error": "The selected ground was not found."
            }), 404

        user = connection.execute("""
            SELECT email FROM users WHERE id = ?
        """, (session["user_id"],)).fetchone()

        if user is None:
            session.clear()
            return jsonify({"error": "Please log in again."}), 401

        try:
            cursor = connection.execute("""
                INSERT INTO bookings
                (ground_id, customer_name, booking_date, time_slot)
                VALUES (?, ?, ?, ?)
            """, (ground_id, customer_name, booking_date, time_slot))

            booking_id = cursor.lastrowid

        except sqlite3.IntegrityError:
            return jsonify({
                "error": "Sorry, this ground is already booked for that date and time. Please choose another slot."
            }), 409

    email_sent = send_email(
        user["email"],
        "Your GroundBook Booking is Confirmed!",
        f"""
Hello {customer_name},

Your sports ground booking is confirmed!

Booking ID: {booking_id}
Ground: {ground["name"]}
Location: {ground["location"]}
Date: {booking_date}
Time: {time_slot}
Price per hour: Rs. {ground["price_per_hour"]}

Thank you for choosing GroundBook!

Enjoy your game!

Team GroundBook
"""
    )

    return jsonify({
        "message": "Booking confirmed",
        "booking_id": booking_id,
        "ground_id": ground_id,
        "booking_date": booking_date,
        "time_slot": time_slot,
        "email_sent": email_sent
    }), 201
if __name__ == "__main__":
    initialize_database()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
