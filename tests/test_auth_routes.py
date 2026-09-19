import pytest
from app import create_app
from database import db
from models import User, Organization


@pytest.fixture
def test_client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_password_hashing():
    user = User(name="Test User", email="test@example.com", account_type="INDIVIDUAL")
    user.set_password("SecurePassword123")

    assert user.password_hash != "SecurePassword123"
    assert user.check_password("SecurePassword123") is True
    assert user.check_password("WrongPassword") is False


def test_individual_registration_and_login(test_client):
    # Register individual
    reg_response = test_client.post(
        "/auth/register",
        data={
            "account_type": "INDIVIDUAL",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )
    assert reg_response.status_code == 200
    assert b"Welcome, Jane Doe" in reg_response.data

    # Access protected individual dashboard
    dash_resp = test_client.get("/individual/dashboard")
    assert dash_resp.status_code == 200
    assert b"Your Digital Carbon Footprint" in dash_resp.data

    # Attempt to access organization dashboard with individual account
    org_resp = test_client.get("/organization/dashboard", follow_redirects=True)
    assert b"reserved for Organization accounts" in org_resp.data


def test_organization_registration(test_client):
    reg_response = test_client.post(
        "/auth/register",
        data={
            "account_type": "ORGANIZATION",
            "name": "Admin John",
            "email": "admin@techcorp.com",
            "password": "TechPassword123",
            "confirm_password": "TechPassword123",
            "org_name": "TechCorp Innovations",
            "industry": "IT / Software",
            "organization_size": "51-200",
        },
        follow_redirects=True,
    )
    assert reg_response.status_code == 200
    assert b"TechCorp Innovations" in reg_response.data

    # Organization dashboard accessible
    dash_resp = test_client.get("/organization/dashboard")
    assert dash_resp.status_code == 200
    assert b"Organization Digital Sustainability Overview" in dash_resp.data

    # Individual dashboard forbidden for org user
    ind_resp = test_client.get("/individual/dashboard", follow_redirects=True)
    assert b"reserved for Individual accounts" in ind_resp.data


def test_unauthenticated_protection(test_client):
    resp = test_client.get("/individual/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_separate_login_pages_get(test_client):
    # Test GET on individual login
    resp_ind = test_client.get("/auth/login/individual")
    assert resp_ind.status_code == 200
    assert b"Individual Sign In" in resp_ind.data
    assert b"Personal Carbon Analytics" in resp_ind.data

    # Test GET on organization login
    resp_org = test_client.get("/auth/login/organization")
    assert resp_org.status_code == 200
    assert b"Organization Sign In" in resp_org.data
    assert b"Digital Sustainability Analytics" in resp_org.data

    # Test backward-compatible generic login
    resp_gen = test_client.get("/auth/login")
    assert resp_gen.status_code == 200

    # Test top-level convenience alias redirects
    alias_ind = test_client.get("/login/individual", follow_redirects=False)
    assert alias_ind.status_code in (301, 302)
    assert "/auth/login/individual" in alias_ind.headers["Location"]

    alias_org = test_client.get("/login/organization", follow_redirects=False)
    assert alias_org.status_code in (301, 302)
    assert "/auth/login/organization" in alias_org.headers["Location"]


def test_separate_login_flow(test_client):
    # 1. Register individual user
    test_client.post(
        "/auth/register",
        data={
            "account_type": "INDIVIDUAL",
            "name": "David Miller",
            "email": "david@personal.org",
            "password": "DavidPassword123",
            "confirm_password": "DavidPassword123",
        },
        follow_redirects=True,
    )
    test_client.get("/auth/logout")

    # 2. Sign in via /auth/login/individual
    ind_login = test_client.post(
        "/auth/login/individual",
        data={"email": "david@personal.org", "password": "DavidPassword123"},
        follow_redirects=True,
    )
    assert ind_login.status_code == 200
    assert b"Your Digital Carbon Footprint" in ind_login.data
    test_client.get("/auth/logout")

    # 3. Register organization user
    test_client.post(
        "/auth/register",
        data={
            "account_type": "ORGANIZATION",
            "name": "Org Admin",
            "email": "admin@greencorp.com",
            "password": "AdminPassword123",
            "confirm_password": "AdminPassword123",
            "org_name": "GreenCorp Global",
            "industry": "IT / Software",
            "organization_size": "51-200",
        },
        follow_redirects=True,
    )
    test_client.get("/auth/logout")

    # 4. Sign in via /auth/login/organization
    org_login = test_client.post(
        "/auth/login/organization",
        data={"email": "admin@greencorp.com", "password": "AdminPassword123"},
        follow_redirects=True,
    )
    assert org_login.status_code == 200
    assert b"Organization Digital Sustainability Overview" in org_login.data
    test_client.get("/auth/logout")

    # 5. Test portal mismatch protection
    mismatch_1 = test_client.post(
        "/auth/login/organization",
        data={"email": "david@personal.org", "password": "DavidPassword123"},
        follow_redirects=True,
    )
    assert b"Individual / Personal account" in mismatch_1.data

    mismatch_2 = test_client.post(
        "/auth/login/individual",
        data={"email": "admin@greencorp.com", "password": "AdminPassword123"},
        follow_redirects=True,
    )
    assert b"Organization / Company" in mismatch_2.data
