from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200


def test_login_page():
    response = client.get("/login.html")
    assert response.status_code == 200


def test_listing_page():
    response = client.get("/listing.html")
    assert response.status_code == 200


def test_seller_page():
    response = client.get("/seller.html")
    assert response.status_code == 200


def test_sell_page():
    response = client.get("/sell.html")
    assert response.status_code == 200


def test_get_listings():
    response = client.get("/listings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_invalid_listing():
    response = client.get("/listings/999999")
    assert response.status_code == 404

def test_invalid_student_id():
    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "student_id": "INVALID",
            "whatsapp": "9876543210",
            "password": "password123",
            "role": "buyer",
        },
        files={
            "id_card": ("id.jpg", b"fake", "image/jpeg"),
            "admission_slip": ("admission.pdf", b"fake", "application/pdf"),
            "passport_photo": ("photo.jpg", b"fake", "image/jpeg"),
        }
    )

    assert response.status_code == 400


def test_invalid_login():
    response = client.post(
        "/login",
        json={
            "student_id": "26MCA00PY0001",
            "password": "wrongpassword"
        }
    )

    assert response.status_code in [401, 403]


def test_upload_image():
    response = client.post(
        "/upload-image",
        files={"file": ("test.png", b"\x89PNG\r\n\x1a\nfakeimagebytes", "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "image_url" in data
    assert data["image_url"].startswith("/static/uploads/")


def test_admin_invalid_key():
    response = client.get(
        "/admin/pending-users",
        headers={"X-Admin-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_admin_valid_key():
    import os
    admin_key = os.getenv("CAMPUSRIDE_ADMIN_KEY", "campusride-admin-2026")
    response = client.get(
        "/admin/pending-users",
        headers={"X-Admin-Key": admin_key}
    )
    assert response.status_code == 200
    assert "users" in response.json()