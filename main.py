from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import os
import uuid
import hashlib
import secrets
import re

app = FastAPI(title="CampusRide")

ADMIN_KEY = os.getenv("CAMPUSRIDE_ADMIN_KEY", "campusride-admin-2026")

os.makedirs("static/uploads", exist_ok=True)
os.makedirs("private_uploads/verification", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================
# DATABASE
# =============================

def get_db():
    conn = sqlite3.connect("campusride.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = get_db()

    # Listings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            purchase_date TEXT,
            condition TEXT,
            description TEXT,
            whatsapp TEXT NOT NULL,
            image_url TEXT,
            seller_name TEXT,
            hostel TEXT
        )
    """)

    # Messages table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            offer_price REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            whatsapp TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            id_card_path TEXT,
            admission_slip_path TEXT,
            passport_photo_path TEXT,
            approved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def upgrade_database():

    conn = get_db()

    columns = [
        "seller_name TEXT",
        "hostel TEXT",
        "seller_student_id TEXT"
    ]

    for column in columns:
        try:
            conn.execute(
                f"ALTER TABLE listings ADD COLUMN {column}"
            )
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


create_tables()
upgrade_database()


# =============================
# DATA MODELS
# =============================

class Listing(BaseModel):

    title: str
    category: str
    price: float
    purchase_date: str
    condition: str
    description: str
    whatsapp: str
    seller_name: str
    hostel: str
    seller_student_id: str
    image_url: str = ""


class Message(BaseModel):

    listing_id: int
    sender: str
    message: str
    offer_price: float | None = None

# =============================
# PASSWORD SECURITY
# =============================

def hash_password(password: str) -> str:

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_password: str) -> bool:

    try:
        salt, stored_hash = stored_password.split("$")

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000
        ).hex()

        return secrets.compare_digest(
            password_hash,
            stored_hash
        )

    except Exception:
        return False

def validate_student_id(student_id: str):
    pattern = r"^26MCA00PY00(0[1-9]|[1-7][0-9]|81)$"
    return re.fullmatch(pattern, student_id) is not None


# =============================
# STUDENT REGISTRATION
# =============================

@app.post("/register")
async def register_student(
    name: str = Form(...),
    student_id: str = Form(...),
    whatsapp: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    id_card: UploadFile = File(...),
    admission_slip: UploadFile = File(...),
    passport_photo: UploadFile = File(...)
):

    # Check student ID
    if not validate_student_id(student_id):

        raise HTTPException(
            status_code=400,
            detail="Invalid student ID. Use 26MCA00PY0001 to 26MCA00PY0081."
        )


    # Check role
    if role not in ["buyer", "seller"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role."
        )


    # Check password
    if len(password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )


    conn = get_db()


    # Check if student already registered
    existing = conn.execute(
        "SELECT id FROM users WHERE student_id = ?",
        (student_id,)
    ).fetchone()


    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Student ID is already registered."
        )


    # =============================
    # SAVE DOCUMENTS
    # =============================

    files = {
        "id_card": id_card,
        "admission_slip": admission_slip,
        "passport_photo": passport_photo
    }


    saved_paths = {}


    for field_name, file in files.items():

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf"
        ]


        if file.content_type not in allowed_types:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {field_name}."
            )


        contents = await file.read()


        # Maximum 5 MB
        if len(contents) > 5 * 1024 * 1024:

            conn.close()

            raise HTTPException(
                status_code=400,
                detail=f"{field_name} must be smaller than 5 MB."
            )


        extension = os.path.splitext(
            file.filename
        )[1].lower()


        filename = (
            f"{student_id}_{field_name}_{uuid.uuid4()}"
            f"{extension}"
        )


        filepath = os.path.join(
            "private_uploads",
            "verification",
            filename
        )


        with open(filepath, "wb") as buffer:

            buffer.write(contents)


        saved_paths[field_name] = filepath


    # =============================
    # SAVE USER
    # =============================

    password_hash = hash_password(password)


    conn.execute("""
        INSERT INTO users
        (
            name,
            student_id,
            whatsapp,
            password_hash,
            role,
            id_card_path,
            admission_slip_path,
            passport_photo_path,
            approved
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        student_id,
        whatsapp,
        password_hash,
        role,
        saved_paths["id_card"],
        saved_paths["admission_slip"],
        saved_paths["passport_photo"],
        0
    ))


    conn.commit()
    conn.close()


    return {
        "message": "Registration submitted successfully.",
        "status": "pending"
    }


# =============================
# LOGIN
# =============================

class LoginRequest(BaseModel):
    student_id: str
    password: str


@app.post("/login")
def login_student(data: LoginRequest):

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE student_id = ?
    """, (
        data.student_id,
    )).fetchone()

    conn.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid student ID or password."
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid student ID or password."
        )

    if user["approved"] != 1:
        raise HTTPException(
            status_code=403,
            detail="Your account is waiting for verification."
        )

    return {
        "message": "Login successful",
        "user": {
            "name": user["name"],
            "student_id": user["student_id"],
            "whatsapp": user["whatsapp"],
            "role": user["role"]
        }
    }

# =============================
# ADMIN VERIFICATION
# =============================

def check_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key."
        )


@app.get("/admin/pending-users")
def get_pending_users(
    x_admin_key: str = Header(...)
):
    check_admin(x_admin_key)

    conn = get_db()

    users = conn.execute("""
        SELECT
            id,
            name,
            student_id,
            whatsapp,
            role,
            id_card_path,
            admission_slip_path,
            passport_photo_path,
            approved,
            created_at
        FROM users
        WHERE approved = 0
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return {
        "users": [dict(user) for user in users]
    }


@app.post("/admin/approve/{user_id}")
def approve_user(
    user_id: int,
    x_admin_key: str = Header(...)
):
    check_admin(x_admin_key)

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    conn.execute("""
        UPDATE users
        SET approved = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return {
        "message": "User approved successfully."
    }


@app.post("/admin/reject/{user_id}")
def reject_user(
    user_id: int,
    x_admin_key: str = Header(...)
):
    check_admin(x_admin_key)

    conn = get_db()

    user = conn.execute(
        "SELECT id FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Registration rejected."
    }


@app.get("/admin/document/{user_id}/{document_type}")
def get_verification_document(
    user_id: int,
    document_type: str,
    x_admin_key: str = Header(...)
):
    check_admin(x_admin_key)

    allowed_documents = {
        "id_card": "id_card_path",
        "admission_slip": "admission_slip_path",
        "passport_photo": "passport_photo_path"
    }

    if document_type not in allowed_documents:
        raise HTTPException(
            status_code=400,
            detail="Invalid document type."
        )

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    filepath = user[allowed_documents[document_type]]

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return FileResponse(filepath)

# =============================
# PAGES
# =============================

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/listing.html")
def listing_page():
    return FileResponse("static/listing.html")

@app.get("/my-listings")
def get_my_listings(
    student_id: str
):
    conn = get_db()

    listings = conn.execute("""
        SELECT *
        FROM listings
        WHERE whatsapp = (
            SELECT whatsapp
            FROM users
            WHERE student_id = ?
        )
        ORDER BY id DESC
    """, (student_id,)).fetchall()

    conn.close()

    return [dict(listing) for listing in listings]

@app.get("/seller.html")
def seller_page():
    return FileResponse("static/seller.html")


@app.get("/sell.html")
def sell_page():
    return FileResponse("static/sell.html")


@app.get("/login.html")
def login_page():
    return FileResponse("static/login.html")

@app.get("/admin.html")
def admin_page():
    return FileResponse("static/admin.html")


# =============================
# UPLOAD IMAGE
# =============================

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):

    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed."
        )

    contents = await file.read()

    # Maximum 5 MB
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 5 MB."
        )

    extension = os.path.splitext(file.filename)[1]

    filename = f"{uuid.uuid4()}{extension}"

    filepath = os.path.join(
        "static",
        "uploads",
        filename
    )

    with open(filepath, "wb") as buffer:
        buffer.write(contents)

    return {
        "image_url": f"/static/uploads/{filename}"
    }

# =============================
# CREATE LISTING
# =============================

@app.post("/listings")
def create_listing(listing: Listing):

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO listings
        (
            title,
            category,
            price,
            purchase_date,
            condition,
            description,
            whatsapp,
            seller_name,
            hostel,
            seller_student_id,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        (
            listing.title,
            listing.category,
            listing.price,
            listing.purchase_date,
            listing.condition,
            listing.description,
            listing.whatsapp,
            listing.seller_name,
            listing.hostel,
            listing.seller_student_id,
            listing.image_url
        )
    ))

    conn.commit()

    listing_id = cursor.lastrowid

    conn.close()

    return {
        "message": "Listing created successfully",
        "listing_id": listing_id
    }


# =============================
# GET ALL LISTINGS
# =============================

@app.get("/listings")
def get_listings():

    conn = get_db()

    listings = conn.execute(
        "SELECT * FROM listings ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return [dict(listing) for listing in listings]


# =============================
# GET ONE LISTING
# =============================

@app.get("/listings/{listing_id}")
def get_listing(listing_id: int):

    conn = get_db()

    listing = conn.execute(
        "SELECT * FROM listings WHERE id = ?",
        (listing_id,)
    ).fetchone()

    conn.close()

    if listing is None:
        raise HTTPException(
            status_code=404,
            detail="Listing not found"
        )

    return dict(listing)


# =============================
# SEND MESSAGE
# =============================

@app.post("/messages")
def send_message(msg: Message):

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO messages
        (
            listing_id,
            sender,
            message,
            offer_price
        )
        VALUES (?, ?, ?, ?)
    """, (
        msg.listing_id,
        msg.sender,
        msg.message,
        msg.offer_price
    ))

    conn.commit()

    message_id = cursor.lastrowid

    conn.close()

    return {
        "message": "Message sent successfully",
        "message_id": message_id
    }


# =============================
# GET CHAT MESSAGES
# =============================

@app.get("/messages/{listing_id}")
def get_messages(listing_id: int):

    conn = get_db()

    messages = conn.execute("""
        SELECT *
        FROM messages
        WHERE listing_id = ?
        ORDER BY id ASC
    """, (listing_id,)).fetchall()

    conn.close()

    return [dict(message) for message in messages]