import pytest
from app import create_app
from database import db
from models import User, IndividualCalculation
from visualization import generate_all_individual_charts


@pytest.fixture
def client_with_user():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # Register an individual user
        client.post(
            "/auth/register",
            data={
                "account_type": "INDIVIDUAL",
                "name": "Eco Tester",
                "email": "eco@tester.org",
                "password": "EcoPassword123",
                "confirm_password": "EcoPassword123",
            },
            follow_redirects=True,
        )

        yield client, app
        db.drop_all()


def test_individual_calculation_chart_generation(client_with_user):
    client, app = client_with_user

    # Submit Calculation 1
    resp1 = client.post(
        "/individual/calculator",
        data={
            "laptop_hours": "6.0",
            "smartphone_hours": "3.0",
            "streaming_hours": "2.0",
            "emails": "40",
            "ai_queries": "15",
            "meeting_hours": "2.0",
        },
        follow_redirects=True,
    )
    assert resp1.status_code == 200

    with app.app_context():
        calc1 = IndividualCalculation.query.order_by(IndividualCalculation.id.asc()).first()
        assert calc1 is not None
        calc1_id = calc1.id

        # Verify all 4 chart files created deterministically
        charts_dir = app.config["CHARTS_FOLDER"]
        act_chart1 = charts_dir / f"ind_act_co2_{calc1_id}.png"
        contrib_chart1 = charts_dir / f"ind_contrib_{calc1_id}.png"
        energy_chart1 = charts_dir / f"ind_energy_{calc1_id}.png"
        summary_chart1 = charts_dir / f"ind_summary_{calc1_id}.png"

        assert act_chart1.exists()
        assert contrib_chart1.exists()
        assert energy_chart1.exists()
        assert summary_chart1.exists()

    # Verify Calculation 1 charts displayed on dashboard with generated_charts path
    dash1 = client.get("/individual/dashboard")
    assert dash1.status_code == 200
    assert f"generated_charts/ind_act_co2_{calc1_id}.png".encode() in dash1.data
    assert f"generated_charts/ind_contrib_{calc1_id}.png".encode() in dash1.data
    assert f"generated_charts/ind_energy_{calc1_id}.png".encode() in dash1.data
    assert f"generated_charts/ind_summary_{calc1_id}.png".encode() in dash1.data

    # Verify images return HTTP 200 when requested by browser
    img_resp = client.get(f"/static/generated_charts/ind_act_co2_{calc1_id}.png")
    assert img_resp.status_code == 200
    img_resp4 = client.get(f"/static/generated_charts/ind_summary_{calc1_id}.png")
    assert img_resp4.status_code == 200

    # Submit Calculation 2 (different values)
    resp2 = client.post(
        "/individual/calculator",
        data={
            "laptop_hours": "1.0",
            "smartphone_hours": "1.0",
            "streaming_hours": "0.5",
            "emails": "5",
            "ai_queries": "2",
            "meeting_hours": "0.0",
        },
        follow_redirects=True,
    )
    assert resp2.status_code == 200

    with app.app_context():
        calc2 = IndividualCalculation.query.order_by(IndividualCalculation.id.desc()).first()
        assert calc2 is not None
        calc2_id = calc2.id
        assert calc2_id != calc1_id

        act_chart2 = charts_dir / f"ind_act_co2_{calc2_id}.png"
        summary_chart2 = charts_dir / f"ind_summary_{calc2_id}.png"
        assert act_chart2.exists()
        assert summary_chart2.exists()

    # Visiting dashboard default loads latest calculation (calc2)
    dash_latest = client.get("/individual/dashboard")
    assert dash_latest.status_code == 200
    assert f"ind_act_co2_{calc2_id}.png".encode() in dash_latest.data
    assert f"ind_act_co2_{calc1_id}.png".encode() not in dash_latest.data

    # Visiting historical calculation explicitly via ?calc_id=calc1_id loads calc1 charts
    dash_hist = client.get(f"/individual/dashboard?calc_id={calc1_id}")
    assert dash_hist.status_code == 200
    assert f"ind_act_co2_{calc1_id}.png".encode() in dash_hist.data
    assert f"ind_act_co2_{calc2_id}.png".encode() not in dash_hist.data
    assert b"View Latest Calculation" in dash_hist.data

    # Check history page contains link to specific calc_id analytics
    hist_page = client.get("/individual/history")
    assert hist_page.status_code == 200
    assert f"/individual/dashboard?calc_id={calc1_id}".encode() in hist_page.data
    assert f"/individual/dashboard?calc_id={calc2_id}".encode() in hist_page.data
    assert b"View Analytics" in hist_page.data
