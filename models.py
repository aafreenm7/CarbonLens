from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash, check_password_hash
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(30), nullable=False)  # 'INDIVIDUAL' or 'ORGANIZATION'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = db.relationship("Organization", backref="user", uselist=False, cascade="all, delete-orphan")
    individual_calculations = db.relationship("IndividualCalculation", backref="user", lazy=True, cascade="all, delete-orphan")
    reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_individual(self) -> bool:
        return self.account_type == "INDIVIDUAL"

    def is_organization(self) -> bool:
        return self.account_type == "ORGANIZATION"


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = db.Column(db.String(180), nullable=False)
    admin_name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(80), nullable=False)
    organization_size = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    datasets = db.relationship("Dataset", backref="organization", lazy=True, cascade="all, delete-orphan")
    analyses = db.relationship("Analysis", backref="organization", lazy=True, cascade="all, delete-orphan")


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    row_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(40), default="uploaded")  # 'uploaded', 'cleaned', 'analyzed'
    is_demo = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    analyses = db.relationship("Analysis", backref="dataset", lazy=True, cascade="all, delete-orphan")


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    total_energy_kwh = db.Column(db.Float, nullable=False, default=0.0)
    total_co2e_kg = db.Column(db.Float, nullable=False, default=0.0)
    highest_impact_activity = db.Column(db.String(100), nullable=False, default="Unknown")
    records_count = db.Column(db.Integer, default=0)
    is_demo = db.Column(db.Boolean, default=False)
    summary_json = db.Column(db.Text, nullable=True)  # Stores serialized stats & metrics
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    activities = db.relationship("AnalysisActivity", backref="analysis", lazy=True, cascade="all, delete-orphan")
    departments = db.relationship("AnalysisDepartment", backref="analysis", lazy=True, cascade="all, delete-orphan")

    def get_summary(self) -> dict:
        if self.summary_json:
            try:
                return json.loads(self.summary_json)
            except Exception:
                return {}
        return {}


class AnalysisActivity(db.Model):
    __tablename__ = "analysis_activities"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    activity_name = db.Column(db.String(80), nullable=False)
    energy_kwh = db.Column(db.Float, default=0.0)
    co2e_kg = db.Column(db.Float, default=0.0)
    percentage = db.Column(db.Float, default=0.0)


class AnalysisDepartment(db.Model):
    __tablename__ = "analysis_departments"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    department_name = db.Column(db.String(100), nullable=False)
    records_count = db.Column(db.Integer, default=0)
    energy_kwh = db.Column(db.Float, default=0.0)
    co2e_kg = db.Column(db.Float, default=0.0)
    percentage = db.Column(db.Float, default=0.0)


class IndividualCalculation(db.Model):
    __tablename__ = "individual_calculations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    laptop_hours = db.Column(db.Float, default=0.0)
    smartphone_hours = db.Column(db.Float, default=0.0)
    streaming_hours = db.Column(db.Float, default=0.0)
    emails = db.Column(db.Float, default=0.0)
    ai_queries = db.Column(db.Float, default=0.0)
    meeting_hours = db.Column(db.Float, default=0.0)

    # Calculated metrics
    daily_energy = db.Column(db.Float, default=0.0)  # kWh
    daily_co2e = db.Column(db.Float, default=0.0)    # gCO2e
    monthly_co2e = db.Column(db.Float, default=0.0)  # kgCO2e
    yearly_co2e = db.Column(db.Float, default=0.0)   # kgCO2e

    breakdown_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_breakdown(self) -> dict:
        if self.breakdown_json:
            try:
                return json.loads(self.breakdown_json)
            except Exception:
                return {}
        return {}


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
