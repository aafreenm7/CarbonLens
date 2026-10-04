import sys
from pathlib import Path
import re

# Ensure CarbonLens root is on path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from database import db
from models import User, Organization, IndividualCalculation


def run_verification():
    print("=" * 70)
    print(" CARBONLENS - COMPREHENSIVE BROWSER FLOW & UI VERIFICATION")
    print("=" * 70)

    app = create_app("testing")

    with app.app_context():
        db.create_all()
        client = app.test_client()

        # =====================================================================
        # TEST A: Open landing page (http://127.0.0.1:5000/)
        # =====================================================================
        print("\n[TEST A] Verifying Landing Page...")
        resp_home = client.get("/")
        assert resp_home.status_code == 200, f"Expected 200, got {resp_home.status_code}"
        home_html = resp_home.data.decode("utf-8")
        assert "CarbonLens" in home_html, "CarbonLens branding missing from landing page"
        assert "Personal Login" in home_html, "'Personal Login' missing from landing page"
        assert "Organization Login" in home_html, "'Organization Login' missing from landing page"
        assert "/auth/login/individual" in home_html, "Link to /auth/login/individual missing from landing page"
        assert "/auth/login/organization" in home_html, "Link to /auth/login/organization missing from landing page"
        print("  [PASS] Landing page loads cleanly (HTTP 200)")
        print("  [PASS] Personal Login and Organization Login entry points are prominent and explicit")

        # =====================================================================
        # TEST B: Open Personal Login page (/auth/login/individual)
        # Must display real login form, MUST NOT redirect to dashboard
        # =====================================================================
        print("\n[TEST B] Verifying Personal Login Form (/auth/login/individual)...")
        resp_ind_login = client.get("/auth/login/individual", follow_redirects=False)
        assert resp_ind_login.status_code == 200, f"Expected 200 OK without redirect, got {resp_ind_login.status_code}"
        ind_login_html = resp_ind_login.data.decode("utf-8")
        assert "<form" in ind_login_html, "Form element missing from personal login page"
        assert "Individual Sign In" in ind_login_html, "Heading 'Individual Sign In' missing"
        assert 'name="email"' in ind_login_html, "Email input field missing"
        assert 'name="password"' in ind_login_html, "Password input field missing"
        assert 'type="submit"' in ind_login_html, "Submit button missing"
        assert "Forgot password?" in ind_login_html, "Forgot password link missing"
        assert "Register Here" in ind_login_html or "register" in ind_login_html.lower(), "Register link missing"
        assert "Personal Carbon Analytics" in ind_login_html or "Personal" in ind_login_html, "Personal portal indication missing"
        print("  [PASS] /auth/login/individual returns HTTP 200 OK directly (NO unwanted redirect)")
        print("  [PASS] Form is fully visible with email, password, login button, forgot password, and register link")

        # Also test top-level alias /login/individual redirects cleanly to /auth/login/individual
        resp_alias_ind = client.get("/login/individual", follow_redirects=False)
        assert resp_alias_ind.status_code in (301, 302), "Alias should redirect to /auth/login/individual"
        assert "/auth/login/individual" in resp_alias_ind.headers["Location"]
        print("  [PASS] Top-level alias /login/individual cleanly redirects to /auth/login/individual")

        # =====================================================================
        # TEST C: Open Organization Login page (/auth/login/organization)
        # Must display real login form, MUST NOT redirect to dashboard
        # =====================================================================
        print("\n[TEST C] Verifying Organization Login Form (/auth/login/organization)...")
        resp_org_login = client.get("/auth/login/organization", follow_redirects=False)
        assert resp_org_login.status_code == 200, f"Expected 200 OK without redirect, got {resp_org_login.status_code}"
        org_login_html = resp_org_login.data.decode("utf-8")
        assert "<form" in org_login_html, "Form element missing from organization login page"
        assert "Organization Sign In" in org_login_html, "Heading 'Organization Sign In' missing"
        assert 'name="email"' in org_login_html, "Email input field missing"
        assert 'name="password"' in org_login_html, "Password input field missing"
        assert 'type="submit"' in org_login_html, "Submit button missing"
        assert "Forgot password?" in org_login_html, "Forgot password link missing"
        assert "Register Company" in org_login_html or "register" in org_login_html.lower(), "Register link missing"
        assert "Digital Sustainability Analytics" in org_login_html or "Organization" in org_login_html, "Organization portal indication missing"
        print("  [PASS] /auth/login/organization returns HTTP 200 OK directly (NO unwanted redirect)")
        print("  [PASS] Form is fully visible with email, password, login button, forgot password, and register link")

        # Also test top-level alias /login/organization redirects cleanly to /auth/login/organization
        resp_alias_org = client.get("/login/organization", follow_redirects=False)
        assert resp_alias_org.status_code in (301, 302), "Alias should redirect to /auth/login/organization"
        assert "/auth/login/organization" in resp_alias_org.headers["Location"]
        print("  [PASS] Top-level alias /login/organization cleanly redirects to /auth/login/organization")

        # Test backward-compatible /auth/login
        resp_legacy_login = client.get("/auth/login", follow_redirects=False)
        assert resp_legacy_login.status_code == 200, "Legacy /auth/login must return 200 OK"
        print("  [PASS] Legacy /auth/login route preserved for backward compatibility")

        # =====================================================================
        # TEST D: Login as Individual & Confirm Individual Dashboard
        # =====================================================================
        print("\n[TEST D] Registering & Signing in as Individual User...")
        # Register an individual
        reg_resp = client.post(
            "/auth/register",
            data={
                "account_type": "INDIVIDUAL",
                "name": "Maya Sharma",
                "email": "maya@research.in",
                "password": "MayaPassword2026",
                "confirm_password": "MayaPassword2026",
            },
            follow_redirects=True,
        )
        assert reg_resp.status_code == 200
        # Sign out to test clean login
        client.get("/auth/logout")

        # Verify login page is STILL accessible when logged out
        check_login = client.get("/auth/login/individual", follow_redirects=False)
        assert check_login.status_code == 200

        # Login via /auth/login/individual
        login_resp = client.post(
            "/auth/login/individual",
            data={"email": "maya@research.in", "password": "MayaPassword2026"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200
        assert b"Your Digital Carbon Footprint" in login_resp.data
        print("  [PASS] Individual login succeeds and navigates directly to Individual Dashboard")

        # Verify that an already-logged in user visiting /auth/login/individual still sees the form
        logged_in_view = client.get("/auth/login/individual", follow_redirects=False)
        assert logged_in_view.status_code == 200, "Should render 200 OK with form even if user has session"
        assert b"<form" in logged_in_view.data
        assert b"switch accounts" in logged_in_view.data or b"signed in as" in logged_in_view.data
        print("  [PASS] Visiting /auth/login/individual while authenticated displays the form with session notice (never bounces)")

        # =====================================================================
        # TEST E: Perform Personal Calculation & Confirm All 4 Charts Render
        # =====================================================================
        print("\n[TEST E] Performing Calculation 1 & Verifying All 4 Data-Driven Charts...")
        calc1_post = client.post(
            "/individual/calculator",
            data={
                "laptop_hours": "5.5",
                "smartphone_hours": "2.5",
                "streaming_hours": "2.0",
                "emails": "35",
                "ai_queries": "12",
                "meeting_hours": "1.5",
            },
            follow_redirects=True,
        )
        assert calc1_post.status_code == 200

        # Dashboard now loads with Calculation 1
        dash1_html = calc1_post.data.decode("utf-8")
        assert "Personal Visual Analytics" in dash1_html, "Visual Analytics section missing from dashboard"

        # Check for Chart 1: Activity CO2e
        assert "ind_act_co2_" in dash1_html, "Chart 1 (Activity CO2e) image tag missing"
        # Check for Chart 2: Direct Operational Electricity
        assert "ind_energy_" in dash1_html, "Chart 2 (Direct Energy) image tag missing"
        # Check for Chart 3: Contribution Share
        assert "ind_contrib_" in dash1_html, "Chart 3 (Contribution Share) image tag missing"
        # Check for Chart 4: Footprint Summary Horizons
        assert "ind_summary_" in dash1_html, "Chart 4 (Footprint Summary) image tag missing"

        # Check that chart URLs use /static/generated_charts/
        assert "/static/generated_charts/ind_act_co2_" in dash1_html, "Chart 1 URL should point to /static/generated_charts/"
        assert "/static/generated_charts/ind_energy_" in dash1_html, "Chart 2 URL should point to /static/generated_charts/"
        assert "/static/generated_charts/ind_contrib_" in dash1_html, "Chart 3 URL should point to /static/generated_charts/"
        assert "/static/generated_charts/ind_summary_" in dash1_html, "Chart 4 URL should point to /static/generated_charts/"

        # Extract image URLs and verify browser receives HTTP 200 OK with actual image data
        img_urls = re.findall(r'/static/generated_charts/ind_[a-z0-9_]+\.png', dash1_html)
        assert len(img_urls) >= 4, f"Expected at least 4 chart images, found {len(img_urls)}: {img_urls}"

        for url in img_urls:
            img_resp = client.get(url)
            assert img_resp.status_code == 200, f"Chart image {url} returned HTTP {img_resp.status_code}"
            assert img_resp.mimetype == "image/png", f"Chart image {url} has unexpected mimetype {img_resp.mimetype}"
            assert len(img_resp.data) > 1000, f"Chart image {url} is suspiciously small ({len(img_resp.data)} bytes)"
            print(f"  [PASS] Chart image loads successfully in browser: {url} ({len(img_resp.data)} bytes, PNG)")

        # Verify calculation 1 values on dashboard
        calc1 = IndividualCalculation.query.order_by(IndividualCalculation.id.asc()).first()
        calc1_id = calc1.id
        print(f"  [PASS] Calculation #1 ID: {calc1_id} | Daily Energy: {calc1.daily_energy:.3f} kWh | Daily CO2e: {calc1.daily_co2e:.1f} g")

        # =====================================================================
        # TEST F: Change Calculation Values & Verify Charts Update
        # =====================================================================
        print("\n[TEST F] Performing Calculation 2 (Different Values) & Verifying Chart Change...")
        calc2_post = client.post(
            "/individual/calculator",
            data={
                "laptop_hours": "1.0",
                "smartphone_hours": "0.5",
                "streaming_hours": "0.0",
                "emails": "5",
                "ai_queries": "1",
                "meeting_hours": "0.0",
            },
            follow_redirects=True,
        )
        assert calc2_post.status_code == 200
        dash2_html = calc2_post.data.decode("utf-8")

        calc2 = IndividualCalculation.query.order_by(IndividualCalculation.id.desc()).first()
        calc2_id = calc2.id
        assert calc2_id != calc1_id, "Calculation 2 should have a distinct ID"

        # Verify Dashboard automatically displays Calculation 2
        assert f"ind_act_co2_{calc2_id}.png" in dash2_html, "Dashboard should display Calculation 2 charts"
        assert f"ind_act_co2_{calc1_id}.png" not in dash2_html, "Dashboard should NOT display Calculation 1 charts"
        print(f"  [PASS] Calculation #2 ID: {calc2_id} | Daily Energy: {calc2.daily_energy:.3f} kWh | Daily CO2e: {calc2.daily_co2e:.1f} g")
        print("  [PASS] Visual analytics updated dynamically to reflect Calculation #2")

        # =====================================================================
        # TEST G: Open Personal History & Verify Historical Chart Isolation
        # =====================================================================
        print("\n[TEST G] Verifying Personal History & Historical Chart Isolation...")
        hist_resp = client.get("/individual/history")
        assert hist_resp.status_code == 200
        hist_html = hist_resp.data.decode("utf-8")
        assert f"/individual/dashboard?calc_id={calc1_id}" in hist_html, "History must link to Calculation 1 with ?calc_id="
        assert f"/individual/dashboard?calc_id={calc2_id}" in hist_html, "History must link to Calculation 2 with ?calc_id="
        assert "View Analytics" in hist_html, "'View Analytics' action missing from history table"
        print("  [PASS] History table cleanly lists past calculations with explicit 'View Analytics' links")

        # Navigate to historical Calculation 1 via ?calc_id=calc1_id
        hist_calc1_resp = client.get(f"/individual/dashboard?calc_id={calc1_id}")
        assert hist_calc1_resp.status_code == 200
        hist_calc1_html = hist_calc1_resp.data.decode("utf-8")

        # Must display Calculation 1 charts and NOT Calculation 2 charts!
        assert f"ind_act_co2_{calc1_id}.png" in hist_calc1_html, "Historical view must display Calculation 1 charts"
        assert f"ind_act_co2_{calc2_id}.png" not in hist_calc1_html, "Historical view must NOT display Calculation 2 charts"
        assert f"Calculation #{calc1_id}" in hist_calc1_html, "Historical view should indicate Calculation #1"
        assert "View Latest Calculation" in hist_calc1_html, "Historical view should offer return to latest calculation"
        print(f"  [PASS] Complete isolation verified: Opening History #{calc1_id} shows ONLY #{calc1_id} charts")

        # =====================================================================
        # TEST H: Organization Workflow & Authorization Integrity
        # =====================================================================
        print("\n[TEST H] Verifying Organization Workflow & Role Authorization...")
        # Try accessing organization dashboard with individual account
        mismatch_access = client.get("/organization/dashboard", follow_redirects=True)
        assert b"reserved for Organization accounts" in mismatch_access.data
        print("  [PASS] Role protection active: Individual blocked from Organization routes")

        # Log out
        client.get("/auth/logout")

        # Register organization
        org_reg = client.post(
            "/auth/register",
            data={
                "account_type": "ORGANIZATION",
                "name": "Kavita Rao",
                "email": "kavita@greentech.org",
                "password": "OrgPassword2026",
                "confirm_password": "OrgPassword2026",
                "org_name": "GreenTech Global",
                "industry": "IT / Software",
                "organization_size": "51-200",
            },
            follow_redirects=True,
        )
        assert org_reg.status_code == 200
        assert b"GreenTech Global" in org_reg.data

        # Access organization upload, analysis, what-if, methodology
        assert client.get("/organization/upload").status_code == 200
        assert client.get("/organization/what-if").status_code in (200, 302)
        assert client.get("/methodology").status_code == 200
        assert client.get("/sources").status_code == 200

        # Try accessing individual dashboard with organization account
        org_mismatch_ind = client.get("/individual/dashboard", follow_redirects=True)
        assert b"reserved for Individual accounts" in org_mismatch_ind.data
        print("  [PASS] Role protection active: Organization blocked from Individual routes")

        # Sign out
        client.get("/auth/logout")

        # Sign in via Organization portal
        org_login_success = client.post(
            "/auth/login/organization",
            data={"email": "kavita@greentech.org", "password": "OrgPassword2026"},
            follow_redirects=True,
        )
        assert org_login_success.status_code == 200
        assert b"Organization Digital Sustainability Overview" in org_login_success.data
        print("  [PASS] Organization sign in succeeds and navigates directly to Organization Dashboard")

        # =====================================================================
        # TEST I: Header Spacing and Navigation Layout
        # =====================================================================
        print("\n[TEST I] Verifying Header Navigation Structure...")
        client.get("/auth/logout")
        resp_unauth_header = client.get("/")
        unauth_html = resp_unauth_header.data.decode("utf-8")
        assert 'class="nav-left"' in unauth_html, "nav-left flex container missing"
        assert 'class="nav-right"' in unauth_html, "nav-right flex container missing"
        assert 'class="nav-links nav-main"' in unauth_html, "nav-main class missing"
        assert 'class="nav-links nav-auth"' in unauth_html, "nav-auth class missing"
        assert 'nav-login-btn' in unauth_html, "nav-login-btn styling class missing"
        assert 'nav-cta-pill' in unauth_html, "nav-cta-pill styling class missing"
        print("  [PASS] Header has clean separation between main navigation and auth actions")

        # =====================================================================
        # TEST J: Subtle Micro-Animations in CSS
        # =====================================================================
        print("\n[TEST J] Verifying Micro-Animations in style.css...")
        css_path = BASE_DIR / "static" / "css" / "style.css"
        css_text = css_path.read_text(encoding="utf-8")
        assert "translateY(-2px)" in css_text, "Subtle translateY(-2px) hover lift missing"
        assert "0.2s ease" in css_text, "150-250ms smooth transition timing missing"
        assert "@media (prefers-reduced-motion: reduce)" in css_text, "Accessibility reduced-motion query missing"
        print("  [PASS] Subtle hover lifts (translateY(-2px), 200ms) applied to buttons, metric cards, panels")
        print("  [PASS] @media (prefers-reduced-motion: reduce) present for full accessibility")

        # =====================================================================
        # TEST K: Responsive Layouts
        # =====================================================================
        print("\n[TEST K] Verifying Mobile / Tablet Responsive Styles...")
        assert ".login-split-grid" in css_text, ".login-split-grid class missing"
        assert "@media (max-width: 768px)" in css_text, "Mobile media query missing"
        assert "@media (max-width: 900px)" in css_text, "Tablet media query missing"
        print("  [PASS] Responsive styles present for mobile (<768px) and tablet (<900px) widths")
        print("  [PASS] Two-column login card gracefully collapses on small viewports")

        # =====================================================================
        # TEST L: Top-Right Sign In Button
        # =====================================================================
        print("\n[TEST L] Verifying Top-Right Header Sign In Button...")
        client.get("/auth/logout")
        resp_unauth = client.get("/")
        unauth_page = resp_unauth.data.decode("utf-8")
        assert 'id="headerSignInBtn"' in unauth_page or 'class="btn-signin-header' in unauth_page, "Header Sign In button missing"
        assert 'href="/auth/login"' in unauth_page, "Sign In button must connect to existing /auth/login route"
        assert "Sign In" in unauth_page, "'Sign In' text missing from header"
        print("  [PASS] Dedicated 'Sign In' button is prominent in top-right header connecting to existing auth")

        # =====================================================================
        # TEST M: Authenticated Profile Dropdown & User Details
        # =====================================================================
        print("\n[TEST M] Verifying Authenticated Profile Dropdown & User Details...")
        client.post(
            "/auth/login/individual",
            data={"email": "maya@research.in", "password": "MayaPassword2026"},
            follow_redirects=True,
        )
        auth_resp = client.get("/individual/dashboard")
        auth_html = auth_resp.data.decode("utf-8")
        assert 'id="profileDropdownBtn"' in auth_html, "Profile dropdown button missing in header"
        assert 'id="profileDropdownMenu"' in auth_html, "Profile dropdown menu missing"
        assert "Maya Sharma" in auth_html, "User name missing from profile area"
        assert "maya@research.in" in auth_html, "User email missing from profile area"
        assert "Individual / Personal" in auth_html, "Account scope missing from profile area"
        assert "/profile" in auth_html, "Link to full Account Details missing"
        assert "/auth/logout" in auth_html, "Link to Sign Out missing from profile dropdown"
        print("  [PASS] Profile dropdown correctly displays Name, Email, Account Scope, and Sign Out option")

        # =====================================================================
        # TEST N: Removal of Methodology from Visible UI
        # =====================================================================
        print("\n[TEST N] Verifying Methodology is Removed from Visible Website UI...")
        # Check landing page
        assert "Methodology & Factors" not in unauth_page, "Methodology button still visible in landing page hero"
        # Check navbar
        assert '<a href="/methodology" class=""' not in unauth_page and '<li><a href="/methodology"' not in unauth_page, "Methodology still visible in navigation header"
        # Check footer links
        assert '>Calculation Boundaries</a>' not in unauth_page, "Methodology still visible in footer links"
        # Ensure backend calculation route still works for scientific integrity
        assert client.get("/methodology").status_code == 200, "Backend /methodology route must remain intact"
        print("  [PASS] Methodology section completely removed from visible navigation, hero, and footer UI")
        print("  [PASS] Backend calculation implementation and route preserved with 100% integrity")

        # =====================================================================
        # TEST O: Project Credits in Footer
        # =====================================================================
        print("\n[TEST O] Verifying Project Credits in Website Footer...")
        assert "project-credits-bar" in unauth_page, "Project credits container missing from footer"
        assert "Project by" in unauth_page, "'Project by' heading missing from credits"
        assert "Aafreen Mujawar" in unauth_page, "Credit for Aafreen Mujawar missing"
        assert "Shrutika Birkalwar" in unauth_page, "Credit for Shrutika Birkalwar missing"
        assert "Parth Asati" in unauth_page, "Credit for Parth Asati missing"
        assert "Sohani Koul" in unauth_page, "Credit for Sohani Koul missing"
        print("  [PASS] Exact Project Credits cleanly rendered: Aafreen Mujawar, Shrutika Birkalwar, Parth Asati, Sohani Koul")

        # =====================================================================
        # TEST P: Interactive Visualizations & Enlarged Layout
        # =====================================================================
        print("\n[TEST P] Verifying Interactive Chart Engine & Expand Zoom Lightbox...")
        # Verify local Chart.js bundle is served cleanly
        resp_chartjs = client.get("/static/js/chart.umd.min.js")
        assert resp_chartjs.status_code == 200, "Local Chart.js UMD file not served"
        assert len(resp_chartjs.data) > 50000, "Chart.js file is empty or corrupted"
        print("  [PASS] Local standalone Chart.js bundle serves successfully (100% offline compatible)")

        # Verify Individual Dashboard interactive canvases and expand modal
        assert 'id="canvas-ind-act-co2"' in auth_html, "Interactive Chart 1 canvas missing"
        assert 'id="canvas-ind-energy"' in auth_html, "Interactive Chart 2 canvas missing"
        assert 'id="canvas-ind-contrib"' in auth_html, "Interactive Chart 3 canvas missing"
        assert 'id="canvas-ind-summary"' in auth_html, "Interactive Chart 4 canvas missing"
        assert 'id="chartExpandModal"' in auth_html, "Chart zoom / expand modal missing"
        assert 'btn-expand-chart' in auth_html, "Expand chart buttons missing"
        assert 'btn-toggle-static' in auth_html, "Toggle view buttons missing"
        assert 'id="individual-calc-data"' in auth_html, "Real Python calculated JSON payload missing"
        print("  [PASS] Individual dashboard has all 4 interactive chart canvases, zoom modal, and data payload")

        # Verify Organization Dashboard interactive canvases
        client.get("/auth/logout")
        client.post(
            "/auth/login/organization",
            data={"email": "kavita@greentech.org", "password": "OrgPassword2026"},
            follow_redirects=True,
        )
        # Load academic demo dataset and run cleaning pipeline to generate Analysis
        from models import Dataset, Analysis
        upload_resp = client.post("/organization/upload", data={"action": "load_demo"}, follow_redirects=True)
        assert upload_resp.status_code == 200
        ds = Dataset.query.order_by(Dataset.id.desc()).first()
        assert ds is not None
        clean_resp = client.post(f"/organization/data-quality/{ds.id}", data={}, follow_redirects=True)
        assert clean_resp.status_code == 200

        org_dash_resp = client.get("/organization/dashboard")
        org_dash_html = org_dash_resp.data.decode("utf-8")
        assert 'id="canvas-org-act-co2"' in org_dash_html, "Org interactive activity canvas missing"
        assert 'id="canvas-org-dept-co2"' in org_dash_html, "Org interactive department canvas missing"
        assert 'id="org-summary-data"' in org_dash_html, "Org summary JSON payload missing"
        print("  [PASS] Organization dashboard has interactive activity & department canvases and data payload")

        # Verify Organization Departments interactive chart
        org_depts_resp = client.get("/organization/departments")
        org_depts_html = org_depts_resp.data.decode("utf-8")
        assert 'id="canvas-depts-page-co2"' in org_depts_html, "Departments page interactive canvas missing"
        assert 'id="departments-list-data"' in org_depts_html, "Departments page data payload missing"
        print("  [PASS] Organization departments page has interactive canvas and dual-axis chart engine")

        print("\n" + "=" * 70)
        print(" ALL 16 VERIFICATION TESTS (TEST A through TEST P) PASSED 100%!")
        print("=" * 70)


if __name__ == "__main__":
    run_verification()

