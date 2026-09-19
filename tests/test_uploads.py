import io
import pytest
from app import create_app
from database import db


@pytest.fixture
def org_client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        client = app.test_client()
        # Register and log in organization
        client.post(
            "/auth/register",
            data={
                "account_type": "ORGANIZATION",
                "name": "Org Admin",
                "email": "org@example.com",
                "password": "Password123",
                "confirm_password": "Password123",
                "org_name": "Test Organization",
                "industry": "IT / Software",
                "organization_size": "51-200",
            },
            follow_redirects=True,
        )
        yield client
        db.drop_all()


def test_load_demo_dataset(org_client):
    resp = org_client.post(
        "/organization/upload",
        data={"action": "load_demo"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Data Quality Audit &amp; Schema Mapping" in resp.data or b"Data Quality Audit & Schema Mapping" in resp.data
    assert b"Demo Dataset" in resp.data


def test_upload_valid_csv(org_client):
    csv_data = (
        "employee_id,department,laptop_hours,smartphone_hours,streaming_hours,emails,ai_queries\n"
        "E1,Engineering,7.0,2.0,1.0,20,15\n"
        "E2,Sales,5.0,4.0,0.5,50,5\n"
    )
    resp = org_client.post(
        "/organization/upload",
        data={"file": (io.BytesIO(csv_data.encode("utf-8")), "activity.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"activity.csv" in resp.data


def test_upload_invalid_extension(org_client):
    resp = org_client.post(
        "/organization/upload",
        data={"file": (io.BytesIO(b"malicious content"), "payload.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Unsupported file format" in resp.data
