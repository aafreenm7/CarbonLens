import io
from pathlib import Path
import pytest
from app import create_app
from database import db
from models import User, Organization, Dataset, Analysis, IndividualCalculation


@pytest.fixture
def client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_complete_e2e_individual_journey(client):
    # 1. Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json["status"] == "online"
    assert health_resp.json["database"] == "healthy"

    # 2. Public pages
    assert client.get("/").status_code == 200
    assert client.get("/methodology").status_code == 200
    assert client.get("/sources").status_code == 200

    # 3. Register individual
    reg = client.post(
        "/auth/register",
        data={
            "account_type": "INDIVIDUAL",
            "name": "Alice Green",
            "email": "alice@ecostudy.org",
            "password": "Ecopassword123",
            "confirm_password": "Ecopassword123",
        },
        follow_redirects=True,
    )
    assert reg.status_code == 200
    assert b"Welcome, Alice Green" in reg.data

    # 4. View empty dashboard
    dash = client.get("/individual/dashboard")
    assert dash.status_code == 200
    assert b"You haven't calculated your footprint yet." in dash.data

    # 5. Submit calculator values
    # Laptop = 4h, Smartphone = 2h, Streaming = 1.5h, Emails = 25, AI = 10
    calc_resp = client.post(
        "/individual/calculator",
        data={
            "laptop_hours": "4.0",
            "smartphone_hours": "2.0",
            "streaming_hours": "1.5",
            "emails": "25",
            "ai_queries": "10",
            "meeting_hours": "5.0",
        },
        follow_redirects=True,
    )
    assert calc_resp.status_code == 200
    assert b"Your footprint has been calculated." in calc_resp.data

    # 6. Verify dashboard displays genuine calculated numbers
    dash_updated = client.get("/individual/dashboard")
    assert dash_updated.status_code == 200
    assert b"Estimated Today" in dash_updated.data
    # 4h laptop = 142g, 2h phone = 2.84g, 1.5h stream = 54g, 25 emails = 7.5g, 10 ai = 2.2g
    # Total daily = ~208.5g
    assert b"208.5" in dash_updated.data or b"208" in dash_updated.data
    # Direct energy = 0.2 + 0.004 + 0.0031 = 0.207 kWh
    assert b"0.207" in dash_updated.data

    # 7. Verify history page
    hist = client.get("/individual/history")
    assert hist.status_code == 200
    assert b"0.207 kWh" in hist.data

    # 8. Verify insights page
    ins = client.get("/individual/insights")
    assert ins.status_code == 200
    assert b"Primary Impact" in ins.data

    # 9. Verify profile page
    prof = client.get("/profile")
    assert prof.status_code == 200
    assert b"Alice Green" in prof.data
    assert b"INDIVIDUAL" in prof.data


def test_complete_e2e_organization_journey(client):
    # 1. Register Organization
    reg = client.post(
        "/auth/register",
        data={
            "account_type": "ORGANIZATION",
            "name": "Sarah Connor",
            "email": "sarah@cyberdyne.io",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123",
            "org_name": "Cyberdyne Sustainability Lab",
            "industry": "IT / Software",
            "organization_size": "51-200",
        },
        follow_redirects=True,
    )
    assert reg.status_code == 200
    assert b"Cyberdyne Sustainability Lab" in reg.data

    # 2. View empty organization dashboard
    dash = client.get("/organization/dashboard")
    assert dash.status_code == 200
    assert b"No activity dataset has been analysed yet." in dash.data

    # 3. Load demo dataset
    load_demo = client.post(
        "/organization/upload",
        data={"action": "load_demo"},
        follow_redirects=True,
    )
    assert load_demo.status_code == 200
    assert b"Data Quality Audit" in load_demo.data

    # 4. Trigger Clean & Analyse on the dataset
    ds = Dataset.query.first()
    assert ds is not None

    clean_resp = client.post(
        f"/organization/data-quality/{ds.id}",
        data={},  # Accept auto-detected mappings
        follow_redirects=True,
    )
    assert clean_resp.status_code == 200
    assert b"Exploratory Data Analysis &amp; Statistical Modeling" in clean_resp.data or b"Exploratory Data Analysis" in clean_resp.data

    # 5. Verify analysis object created in database
    analysis_obj = Analysis.query.filter_by(dataset_id=ds.id).first()
    assert analysis_obj is not None
    assert analysis_obj.total_co2e_kg > 0
    assert analysis_obj.total_energy_kwh > 0
    assert analysis_obj.records_count > 0

    # 6. Verify organization dashboard now renders active KPIs and charts
    dash_active = client.get("/organization/dashboard")
    assert dash_active.status_code == 200
    assert b"Estimated Monthly CO" in dash_active.data
    assert b"Emissions by Activity" in dash_active.data

    # 7. Verify departments page
    depts_resp = client.get("/organization/departments")
    assert depts_resp.status_code == 200
    assert b"Detailed Departmental Performance Matrix" in depts_resp.data

    # 8. Verify insights page
    ins_resp = client.get("/organization/insights")
    assert ins_resp.status_code == 200
    assert b"Primary Impact Driver" in ins_resp.data

    # 9. Test What-If Simulator
    whatif_get = client.get("/organization/what-if")
    assert whatif_get.status_code == 200
    assert b"What-If Digital Reduction Simulator" in whatif_get.data

    whatif_post = client.post(
        "/organization/what-if",
        data={
            "laptop_reduction": "20",
            "streaming_reduction": "30",
            "ai_reduction": "25",
            "phone_reduction": "10",
            "email_reduction": "15",
        },
        follow_redirects=True,
    )
    assert whatif_post.status_code == 200
    assert b"Potential Daily Reduction" in whatif_post.data

    # 10. Verify Reports & Exports
    rep_page = client.get("/organization/reports")
    assert rep_page.status_code == 200
    assert b"Digital Sustainability Executive Report" in rep_page.data

    # Test all exports
    csv_clean = client.get(f"/organization/export/cleaned/{analysis_obj.id}")
    assert csv_clean.status_code == 200
    assert "text/csv" in csv_clean.headers["Content-Type"]

    csv_calc = client.get(f"/organization/export/calculated/{analysis_obj.id}")
    assert csv_calc.status_code == 200

    csv_act = client.get(f"/organization/export/activities/{analysis_obj.id}")
    assert csv_act.status_code == 200

    csv_dept = client.get(f"/organization/export/departments/{analysis_obj.id}")
    assert csv_dept.status_code == 200

    pdf_resp = client.get(f"/organization/export/pdf/{analysis_obj.id}")
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["Content-Type"]
    assert len(pdf_resp.data) > 1000
