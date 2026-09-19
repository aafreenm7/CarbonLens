# CarbonLens — Digital Carbon Footprint Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11+-1b4332.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Flask-3.0+-2d6a4f.svg)](https://flask.palletsprojects.com/)
[![DataScience](https://img.shields.io/badge/Pandas%20%7C%20NumPy-Enabled-52b788.svg)](https://pandas.pydata.org/)
[![Database](https://img.shields.io/badge/SQLAlchemy-SQLite%20%2F%20PostgreSQL-74c69d.svg)](https://www.sqlalchemy.org/)

**B.Tech Computer Engineering &mdash; Data Science Capstone Project**  
*A genuine Python Data Science web platform for estimating, auditing, visualizing, and abating digital carbon emissions.*

---

## 1. Executive Summary & Problem Statement

Information and Communications Technology (ICT) accounts for an estimated **2% to 4% of global greenhouse gas emissions**, rivaling commercial aviation. While industrial and transport emissions are frequently audited, the **invisible carbon footprint of digital operations**—arising from employee laptops, mobile devices, video streaming, mass enterprise electronic mail, and generative artificial intelligence (LLM) inference—is seldom measured or transparently understood.

Existing web calculators are predominantly static marketing widgets, proprietary closed-source APIs, or aesthetic mockups with hardcoded percentages. **CarbonLens** addresses this deficit by providing a **production-structured, local-first, authentic Python Data Science web platform**.

---

## 2. Core Python Data Science Pipeline

CarbonLens rejects superficial frontend calculations. The system executes a rigorous end-to-end data science lifecycle:

```text
DATA ACQUISITION (CSV / Excel / Form Input)
       ↓
SCHEMA MAPPING & SYNONYM ALIAS DETECTION
       ↓
DATA QUALITY AUDIT (Duplicates, Missing Values, Range Errors)
       ↓
NON-DESTRUCTIVE CLEANING & IMPUTATION
       ↓
STANDARDIZED PANDAS DATAFRAME CREATION
       ↓
VECTORIZED PYTHON CARBON ENGINE (Physical & Lifecycle Math)
       ↓
STATISTICAL ANALYSIS & DESCRIPTIVE EDA (describe(), IQR)
       ↓
ANALYTICAL VISUALIZATION (Matplotlib & Seaborn)
       ↓
DYNAMIC ALGORITHMIC INSIGHT GENERATION
       ↓
WHAT-IF SCENARIO MODELLING & REDUCTION SIMULATION
       ↓
MULTI-FORMAT REPORTING (Executive PDF & CSV Exports)
```

---

## 3. Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Primary scientific calculation and backend language |
| **Web Framework** | Flask 3.0+, Jinja2 | Application routing, sessions, context processors |
| **Data Science** | Pandas, NumPy | Vectorized series calculations, aggregations, matrix operations |
| **Visualization** | Matplotlib, Seaborn | Publication-grade charts rendered with headless `Agg` backend |
| **Statistical Modeling**| scikit-learn | Optional experimental regression with $R^2$ and MAE evaluation |
| **Database ORM** | SQLAlchemy | Environment-switchable: **SQLite** (local) $\rightarrow$ **PostgreSQL** (production) |
| **Authentication** | Werkzeug Security | PBKDF2:SHA256 password hashing, secure session management |
| **Document Export** | ReportLab, openpyxl | Formal executive PDF reports and Excel parsing |
| **Testing** | pytest | Automated unit tests across all data science modules |

---

## 4. Scientific Methodology & Emission Factors

All calculations are tied to verified peer-reviewed literature, official national electricity regulatory baselines, or explicitly documented project modelling assumptions.

### Verified Emission Factors (`data/emission_factors.csv`)

| Activity | Factor Value | Units | Factor Category | Verified Citation / Regulatory Source |
| :--- | :--- | :--- | :--- | :--- |
| **Indian Electricity Grid** | `0.710` | $\text{kgCO}_2\text{e/kWh}$ | `RESEARCH_BASED` | Central Electricity Authority (CEA), India (FY2024–25 Baseline) |
| **Laptop Active Power** | `50.0` | $\text{Watts}$ | `PROJECT_ASSUMPTION` | Standard enterprise laptop operational baseline |
| **Smartphone Screen Power**| `2.0` | $\text{Watts}$ | `PROJECT_ASSUMPTION` | Average active mobile operational draw |
| **HD Video Streaming** | `36.0` | $\text{gCO}_2\text{e/hour}$ | `RESEARCH_BASED` | International Energy Agency (IEA, 2020) |
| **Electronic Mail** | `0.3` | $\text{gCO}_2\text{e/email}$ | `RESEARCH_BASED` | Updated Berners-Lee life-cycle intensity |
| **Generative AI Queries** | `0.31` | $\text{Wh/query}$ | `RESEARCH_BASED` | Oviedo et al., *Joule* (2026) |

### Mathematical Formulations

1. **Laptop Operational Emissions:**
   $$\text{Energy (kWh)} = \frac{\text{Hours} \times 50\text{ W}}{1000}, \quad \text{CO}_2\text{e (kg)} = \text{Energy (kWh)} \times 0.710$$

2. **Smartphone Operational Emissions:**
   $$\text{Energy (kWh)} = \frac{\text{Hours} \times 2\text{ W}}{1000}, \quad \text{CO}_2\text{e (kg)} = \text{Energy (kWh)} \times 0.710$$

3. **Video Streaming Lifecycle Emissions:**
   $$\text{CO}_2\text{e (kg)} = \frac{\text{Hours} \times 36.0\text{ g}}{1000}$$

4. **Email Communications Emissions:**
   $$\text{CO}_2\text{e (kg)} = \frac{\text{Message Count} \times 0.3\text{ g}}{1000}$$

5. **Generative AI Inference Emissions:**
   $$\text{AI Energy (kWh)} = \frac{\text{Queries} \times 0.31\text{ Wh}}{1000}, \quad \text{CO}_2\text{e (kg)} = \text{AI Energy} \times 0.710$$

6. **Time Horizon Projections:**
   $$\text{Monthly (kg)} = \text{Daily Baseline} \times 30, \quad \text{Yearly (kg)} = \text{Daily Baseline} \times 365$$

### Critical Scientific Safeguard: Double-Counting Prevention
The IEA (2020) video streaming boundary accounts for content distribution networks, data centers, and end-user display power. **CarbonLens explicitly separates device hours from streaming hours so user display electricity is not duplicated.**

---

## 5. Dual Application Modes

### Mode 1: Individual User
- Daily personal digital activity calculator (laptop, mobile, video streaming, email, LLM queries).
- Real-time conversion into direct electricity ($\text{kWh}$) and greenhouse gas footprint ($\text{gCO}_2\text{e}$ / $\text{kgCO}_2\text{e}$).
- Longitudinal historical tracking with timestamped logs.
- Personalized, data-driven reduction guidance.

### Mode 2: Organization Sustainability
- Drag-and-drop ingestion of enterprise CSV and Excel (`.xlsx`) datasets.
- Schema auto-mapping supporting column synonyms (e.g. `laptop_usage`, `stream_time`, `ai_prompts`).
- Transparent cleaning audit: drops exact duplicates, corrects negative inputs, imputes missing values via medians, and flags $1.5 \times \text{IQR}$ outliers without silent data loss.
- Publication charts: CO₂e by Activity, CO₂e by Department, Operational Energy, KDE Distribution, Boxplots, and Correlation Heatmaps.
- Interactive **What-If Scenario Simulator** calculating net percentage reductions.
- Formal executive **ReportLab PDF generator** and multi-format CSV exports.

---

## 6. Project Architecture & Directory Layout

```text
CarbonLens/
│
├── app.py                     # Flask application factory, routes, and error handlers
├── config.py                  # Environment configuration (SQLite default, PostgreSQL ready)
├── database.py                # SQLAlchemy DB instance
├── models.py                  # User, Organization, Dataset, Analysis, IndividualCalculation
├── auth.py                    # Session auth, Werkzeug hashing, role decorators, password reset
├── carbon_engine.py           # Core scientific formulas & emission calculation engine
├── data_cleaning.py           # Data quality audit, alias mapping, outlier & duplicate cleaning
├── analysis.py                # Pandas vectorized analysis, aggregations & scikit-learn ML
├── visualization.py           # Matplotlib & Seaborn academic charts generator (Agg backend)
├── recommendations.py         # Dynamic, data-driven insight engine
├── report_generator.py        # CSV exports and ReportLab executive PDF generation
├── wsgi.py                    # Production WSGI server entry point
│
├── requirements.txt           # Verified Python dependencies
├── README.md                  # Comprehensive documentation and syllabus mapping
├── .env.example               # Environment variables template
├── .gitignore                 # Python and environment ignore rules
├── run.bat                    # Windows one-click startup script
│
├── data/
│   ├── emission_factors.csv   # Scientific factors and assumptions
│   └── demo_activity_data.csv # Realistic academic sample dataset
│
├── uploads/                   # Secure isolated directory for raw datasets
├── exports/                   # Directory for generated CSV and PDF reports
├── instance/                  # Local SQLite database directory
│
├── static/
│   ├── css/style.css          # Restrained environmental laboratory styling
│   ├── js/app.js              # Client-side progressive enhancements (drag-drop, sliders)
│   └── generated_charts/      # Directory for dynamically generated analytical charts
│
├── templates/                 # 23 Jinja2 academic templates
│   ├── base.html              # Role-aware navbar and SDG footer
│   ├── index.html             # Public landing page and pipeline summary
│   ├── methodology.html       # Mathematical proofs and boundary documentation
│   ├── sources.html           # Full bibliography and citation notes
│   ├── profile.html           # User account profile
│   ├── auth/                  # login, register, forgot_password, reset_password
│   ├── individual/            # dashboard, calculator, history, insights
│   ├── organization/          # dashboard, upload, data_quality, analysis, departments, insights, what_if, reports
│   └── errors/                # 404, 500 error pages
│
└── tests/                     # Comprehensive pytest test suite
    ├── __init__.py
    ├── test_carbon_engine.py  # Emission formulas, boundaries, double-counting tests
    ├── test_cleaning.py       # Column aliases, missing values, duplicates, outliers tests
    ├── test_analysis.py       # Aggregations, Pandas describe(), ML safeguard tests
    ├── test_auth_routes.py    # Registration, login, password hashing, role protection tests
    ├── test_uploads.py        # CSV/XLSX parsing, demo dataset, extension security tests
    └── test_reports.py        # CSV exports and ReportLab PDF compilation tests
```

---

## 7. Windows Installation & Local Setup Guide

CarbonLens requires **Python 3.11+** and runs completely locally without external cloud dependencies.

### Step 1: Open Terminal in VS Code
Open PowerShell in the project directory:
```powershell
cd C:\Users\ACER\.gemini\antigravity\scratch\CarbonLens
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Required Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Launch the Local Web Application
```powershell
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

*(Alternatively on Windows, double-click `run.bat` to launch automatically).*

---

## 8. Running Automated Tests

Run the automated pytest test suite:
```powershell
.venv\Scripts\pytest.exe -v
```

All unit and integration tests cover:
- Mathematical accuracy of laptop, mobile, streaming, email, and AI calculations.
- Double-counting prevention safeguards.
- Column alias recognition and non-destructive cleaning reports.
- Inter-departmental aggregations and descriptive statistics.
- Scikit-learn regression safeguards ($N \ge 20$).
- Role-based authorization and Werkzeug password hashing.
- File upload validation and ReportLab PDF generation.

---

## 9. Academic Syllabus Mapping (Computer Engineering & Data Science)

| Curriculum Subject | Implementation in CarbonLens | Key Source Modules |
| :--- | :--- | :--- |
| **Python Programming** | Application factory pattern, custom decorators (`@organization_required`), exception handling, type annotations, context managers. | `app.py`, `auth.py`, `config.py` |
| **Data Structures** | Custom objects, dictionary mappings, inverted synonym lookup indexes, JSON serialization. | `data_cleaning.py`, `models.py` |
| **Pandas** | Vectorized DataFrame operations, missing value handling, column renaming, `groupby()`, `describe()`, `to_csv()`. | `analysis.py`, `data_cleaning.py` |
| **NumPy** | Numerical array manipulation, clipping ranges, mathematical operations. | `analysis.py`, `carbon_engine.py` |
| **Matplotlib & Seaborn** | Headless chart generation (`Agg` backend), bar charts, KDE distributions, boxplots, correlation heatmaps. | `visualization.py` |
| **Data Acquisition** | Safe parsing of CSV and Excel spreadsheets, file size enforcement, secure filename normalization. | `app.py`, `data_cleaning.py` |
| **Data Cleaning & Preprocessing** | Deduplication, negative value coercion, median imputation, $1.5 \times \text{IQR}$ statistical anomaly flagging. | `data_cleaning.py` |
| **Exploratory Data Analysis (EDA)** | Descriptive statistics (mean, median, IQR, std), distribution analysis, correlation matrices. | `analysis.py`, `templates/organization/analysis.html` |
| **Machine Learning** | Optional linear regression with `train_test_split`, MAE and $R^2$ score evaluation, explicit sample size safeguard ($N \ge 20$). | `analysis.py` |
| **Database Management (RDBMS)** | Relational schema modeling with SQLAlchemy ORM, foreign key cascades, transaction rollback safety. | `models.py`, `database.py` |
| **Software Engineering & Testing**| Unit testing with pytest, isolated fixtures, environment-based configuration, production WSGI entry point. | `tests/`, `wsgi.py` |

---

## 10. Production Deployment Readiness

CarbonLens is architected for zero-code-change migration to cloud production (e.g. Render, Railway, Fly.io, Supabase, or AWS):

1. **Database Migration:**  
   Set the `DATABASE_URL` environment variable:
   ```bash
   DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
   ```
   SQLAlchemy automatically handles connection pooling and dialect mapping.
2. **Production WSGI Server:**  
   Run using a WSGI HTTP server:
   ```bash
   gunicorn "wsgi:application" --workers 4 --bind 0.0.0.0:5000
   ```
3. **Health Monitoring:**  
   Use `/health` to probe HTTP status and database connectivity.

---

## 11. Viva-Oriented System Defense Guide

### Q1: Why is laptop electricity not added to video streaming hours?
> **Answer:** Under the International Energy Agency (IEA, 2020) methodology, the 36 gCO₂e/hour streaming emission factor already encompasses data centers, transmission networks, and average client display electricity. Summing separate laptop power with streaming would cause double-counting of the device display load.

### Q2: How does the data cleaning pipeline preserve data integrity?
> **Answer:** The pipeline is non-destructive. It corrects mathematically invalid entries (such as negative hours) while detecting statistical outliers ($1.5 \times \text{IQR}$) as separate analytical flags rather than silently deleting rows. All transformations are recorded in a transparent `CleaningReport`.

### Q3: Why is Machine Learning optional rather than mandatory for calculations?
> **Answer:** Digital carbon accounting is governed by physical and empirical lifecycle conversion factors. A machine learning regression model is trained on activity data only when sufficient observations ($N \ge 20$) exist to explore correlations, but it never replaces the verified scientific calculation engine.

---

## 12. License & Academic Declaration

This project was developed as an academic capstone for the **B.Tech in Computer Engineering (Data Science)** degree. All code and analytical pipelines are licensed under the MIT License.
