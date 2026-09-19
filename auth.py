"""CarbonLens Authentication & Access Control Module.

Implements session-based authentication, Werkzeug password hashing,
role-based authorization decorators, and a functional password-reset workflow.
"""

from functools import wraps
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)
from database import db
from models import User, Organization, PasswordResetToken

auth_bp = Blueprint("auth", __name__)


# -------------------------------------------------------------------------
# Authorization Decorators
# -------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def individual_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an Individual user.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if session.get("account_type") != "INDIVIDUAL":
            flash("This page is reserved for Individual accounts.", "warning")
            return redirect(url_for("organization_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def organization_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an Organization user.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if session.get("account_type") != "ORGANIZATION":
            flash("This page is reserved for Organization accounts.", "warning")
            return redirect(url_for("individual_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        if session.get("account_type") == "ORGANIZATION":
            return redirect(url_for("organization_dashboard"))
        return redirect(url_for("individual_dashboard"))

    if request.method == "POST":
        account_type = request.form.get("account_type", "INDIVIDUAL").strip().upper()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Common validations
        if not name or not email or not password:
            flash("Please complete all required fields.", "danger")
            return render_template("auth/register.html", account_type=account_type)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", account_type=account_type)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/register.html", account_type=account_type)

        # Duplicate email check
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        if account_type == "ORGANIZATION":
            org_name = request.form.get("org_name", "").strip()
            admin_name = request.form.get("admin_name", name).strip()
            industry = request.form.get("industry", "IT / Software").strip()
            org_size = request.form.get("organization_size", "51-200").strip()

            if not org_name:
                flash("Organization name is required.", "danger")
                return render_template("auth/register.html", account_type="ORGANIZATION")

            new_user = User(
                name=admin_name,
                email=email,
                account_type="ORGANIZATION",
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()

            new_org = Organization(
                user_id=new_user.id,
                name=org_name,
                admin_name=admin_name,
                industry=industry,
                organization_size=org_size,
            )
            db.session.add(new_org)
            db.session.commit()

            session.clear()
            session["user_id"] = new_user.id
            session["user_name"] = new_user.name
            session["account_type"] = new_user.account_type
            session["org_id"] = new_org.id
            session["org_name"] = new_org.name

            flash(f"Organization '{org_name}' registered successfully.", "success")
            return redirect(url_for("organization_dashboard"))

        else:  # INDIVIDUAL
            new_user = User(
                name=name,
                email=email,
                account_type="INDIVIDUAL",
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            session.clear()
            session["user_id"] = new_user.id
            session["user_name"] = new_user.name
            session["account_type"] = new_user.account_type

            flash(f"Welcome, {new_user.name}! Your account has been created.", "success")
            return redirect(url_for("individual_dashboard"))

    # GET
    default_type = request.args.get("type", "INDIVIDUAL").upper()
    if default_type not in ["INDIVIDUAL", "ORGANIZATION"]:
        default_type = "INDIVIDUAL"
    return render_template("auth/register.html", account_type=default_type)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_page = request.form.get("next") or request.args.get("next")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login.html", email=email)

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["account_type"] = user.account_type

        if user.is_organization() and user.organization:
            session["org_id"] = user.organization.id
            session["org_name"] = user.organization.name

        flash(f"Signed in as {user.name}.", "success")

        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        if user.is_organization():
            return redirect(url_for("organization_dashboard"))
        return redirect(url_for("individual_dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/login/individual", methods=["GET", "POST"])
def login_individual():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_page = request.form.get("next") or request.args.get("next")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login_individual.html", email=email)

        if user.account_type != "INDIVIDUAL":
            flash("This account is registered as an Organization / Company. Please sign in via the Organization portal.", "warning")
            return render_template("auth/login_individual.html", email=email)

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["account_type"] = user.account_type

        flash(f"Signed in as {user.name}.", "success")

        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("individual_dashboard"))

    return render_template("auth/login_individual.html")


@auth_bp.route("/login/organization", methods=["GET", "POST"])
def login_organization():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_page = request.form.get("next") or request.args.get("next")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login_organization.html", email=email)

        if user.account_type != "ORGANIZATION":
            flash("This account is registered as an Individual / Personal account. Please sign in via the Personal portal.", "warning")
            return render_template("auth/login_organization.html", email=email)

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["account_type"] = user.account_type

        if user.organization:
            session["org_id"] = user.organization.id
            session["org_name"] = user.organization.name

        flash(f"Signed in as {user.name}.", "success")

        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("organization_dashboard"))

    return render_template("auth/login_organization.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


# -------------------------------------------------------------------------
# Password Reset Routes
# -------------------------------------------------------------------------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    dev_reset_url = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate cryptographic token
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            # Invalidate old unused tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id, is_used=False).update(
                {"is_used": True}
            )

            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                is_used=False,
            )
            db.session.add(reset_record)
            db.session.commit()

            # For local academic development, provide the direct reset link
            dev_reset_url = url_for("auth.reset_password", token=raw_token, _external=True)
            flash(
                "Password reset instructions have been generated. (In local development mode, use the link provided below.)",
                "info",
            )
        else:
            # Neutral message to prevent user enumeration
            flash(
                "If an account is associated with that email, reset instructions have been issued.",
                "info",
            )

    return render_template("auth/forgot_password.html", dev_reset_url=dev_reset_url)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now_utc = datetime.now(timezone.utc)

    reset_record = PasswordResetToken.query.filter_by(
        token_hash=token_hash, is_used=False
    ).first()

    if not reset_record:
        flash("Invalid or expired password reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    # Check expiration
    # Ensure timezone awareness for comparison
    record_expires = reset_record.expires_at
    if record_expires.tzinfo is None:
        record_expires = record_expires.replace(tzinfo=timezone.utc)

    if record_expires < now_utc:
        reset_record.is_used = True
        db.session.commit()
        flash("This password reset link has expired. Please request a new one.", "warning")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.get(reset_record.user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(password)
        reset_record.is_used = True
        db.session.commit()

        flash("Your password has been reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
