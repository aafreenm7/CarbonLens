"""CarbonLens — Digital Carbon Footprint Analytics Platform.

Main Flask application factory, route controllers, and lifecycle handlers.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
from werkzeug.utils import secure_filename

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    jsonify,
    abort,
)

from config import config_by_name, BASE_DIR
from database import db
from models import (
    User,
    Organization,
    Dataset,
    Analysis,
    AnalysisActivity,
    AnalysisDepartment,
    IndividualCalculation,
)
from auth import auth_bp, login_required, individual_required, organization_required
import carbon_engine
import data_cleaning
import analysis as analysis_module
import visualization as viz_module
import recommendations as rec_module
import report_generator


def create_app(config_name=None):
    """Application factory for CarbonLens."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure required directories exist
    for folder in [
        app.config["UPLOAD_FOLDER"],
        app.config["EXPORTS_FOLDER"],
        app.config["CHARTS_FOLDER"],
        app.config["DATA_FOLDER"],
        BASE_DIR / "instance",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ---------------------------------------------------------------------
    # Global Context Processor & Template Helpers
    # ---------------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        current_user_obj = None
        if "user_id" in session:
            current_user_obj = db.session.get(User, session["user_id"])

        return {
            "current_user": current_user_obj,
            "session": session,
            "now_year": datetime.now().year,
        }

    # ---------------------------------------------------------------------
    # Public & Information Routes
    # ---------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_redirect():
        return redirect(url_for("auth.login"))

    @app.route("/login/individual")
    def login_individual_redirect():
        return redirect(url_for("auth.login_individual"))

    @app.route("/login/organization")
    def login_organization_redirect():
        return redirect(url_for("auth.login_organization"))

    @app.route("/methodology")
    def methodology():
        return render_template("methodology.html")

    @app.route("/sources")
    def sources():
        return render_template("sources.html")

    @app.route("/profile")
    @login_required
    def profile():
        user = db.session.get(User, session["user_id"])
        if not user:
            session.clear()
            return redirect(url_for("auth.login"))
        return render_template("profile.html", user=user)

    @app.route("/health")
    def health():
        """Health check verifying Flask application and database connectivity."""
        db_status = "healthy"
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        return jsonify({
            "status": "online",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "version": "1.0.0",
        }), 200

    # ---------------------------------------------------------------------
    # Individual User Routes
    # ---------------------------------------------------------------------
    @app.route("/individual/dashboard")
    @individual_required
    def individual_dashboard():
        user_id = session["user_id"]
        calc_id = request.args.get("calc_id", type=int)
        if calc_id:
            calc = IndividualCalculation.query.filter_by(id=calc_id, user_id=user_id).first_or_404()
        else:
            calc = (
                IndividualCalculation.query.filter_by(user_id=user_id)
                .order_by(IndividualCalculation.created_at.desc())
                .first()
            )

        charts = {}
        calc_dict = {}
        if calc:
            calc_dict = calc.get_breakdown() or {}
            calc_dict["daily_co2e_g"] = calc.daily_co2e
            calc_dict["daily_co2e_kg"] = (calc.daily_co2e / 1000.0) if calc.daily_co2e else 0.0
            calc_dict["monthly_co2e_kg"] = calc.monthly_co2e
            calc_dict["yearly_co2e_kg"] = calc.yearly_co2e
            calc_dict["daily_energy_kwh"] = calc.daily_energy
            charts = viz_module.generate_all_individual_charts(
                calc.id, calc_dict, app.config["CHARTS_FOLDER"]
            )

        return render_template("individual/dashboard.html", calc=calc, charts=charts, calc_dict=calc_dict)

    @app.route("/individual/calculator", methods=["GET", "POST"])
    @individual_required
    def individual_calculator():
        if request.method == "POST":
            try:
                laptop_hours = float(request.form.get("laptop_hours", 0) or 0)
                smartphone_hours = float(request.form.get("smartphone_hours", 0) or 0)
                streaming_hours = float(request.form.get("streaming_hours", 0) or 0)
                emails = float(request.form.get("emails", 0) or 0)
                ai_queries = float(request.form.get("ai_queries", 0) or 0)
                meeting_hours = float(request.form.get("meeting_hours", 0) or 0)

                # Validation
                for name, val in [
                    ("Laptop hours", laptop_hours),
                    ("Smartphone hours", smartphone_hours),
                    ("Streaming hours", streaming_hours),
                    ("Emails", emails),
                    ("AI queries", ai_queries),
                    ("Meeting hours", meeting_hours),
                ]:
                    if val < 0:
                        flash(f"{name} cannot be negative.", "danger")
                        return render_template("individual/calculator.html", form_data=request.form)

                if laptop_hours > 24 or smartphone_hours > 24 or streaming_hours > 24:
                    flash("Daily activity hours cannot exceed 24 hours per day.", "danger")
                    return render_template("individual/calculator.html", form_data=request.form)

            except ValueError:
                flash("Please enter valid numeric values.", "danger")
                return render_template("individual/calculator.html", form_data=request.form)

            # Delegate authoritative calculation to Python carbon engine
            results = carbon_engine.calculate_total_emissions(
                laptop_hours=laptop_hours,
                smartphone_hours=smartphone_hours,
                streaming_hours=streaming_hours,
                emails=emails,
                ai_queries=ai_queries,
            )

            # Persist calculation
            calc_record = IndividualCalculation(
                user_id=session["user_id"],
                laptop_hours=laptop_hours,
                smartphone_hours=smartphone_hours,
                streaming_hours=streaming_hours,
                emails=emails,
                ai_queries=ai_queries,
                meeting_hours=meeting_hours,
                daily_energy=results["daily_energy_kwh"],
                daily_co2e=results["daily_co2e_g"],
                monthly_co2e=results["monthly_co2e_kg"],
                yearly_co2e=results["yearly_co2e_kg"],
                breakdown_json=json.dumps(results),
            )
            db.session.add(calc_record)
            db.session.commit()

            try:
                viz_module.generate_all_individual_charts(
                    calc_record.id, results, app.config["CHARTS_FOLDER"]
                )
            except Exception:
                pass

            flash("Your footprint has been calculated.", "success")
            return redirect(url_for("individual_dashboard"))

        return render_template("individual/calculator.html", form_data={})

    @app.route("/individual/history")
    @individual_required
    def individual_history():
        calculations = (
            IndividualCalculation.query.filter_by(user_id=session["user_id"])
            .order_by(IndividualCalculation.created_at.desc())
            .all()
        )
        return render_template("individual/history.html", calculations=calculations)

    @app.route("/individual/insights")
    @individual_required
    def individual_insights():
        latest_calc = (
            IndividualCalculation.query.filter_by(user_id=session["user_id"])
            .order_by(IndividualCalculation.created_at.desc())
            .first()
        )
        insights = []
        if latest_calc:
            calc_dict = latest_calc.get_breakdown()
            insights = rec_module.generate_individual_insights(calc_dict)

        return render_template(
            "individual/insights.html", calc=latest_calc, insights=insights
        )

    # ---------------------------------------------------------------------
    # Organization Routes
    # ---------------------------------------------------------------------
    @app.route("/organization/dashboard")
    @organization_required
    def organization_dashboard():
        org_id = session.get("org_id")
        latest_analysis = (
            Analysis.query.filter_by(organization_id=org_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )
        summary = latest_analysis.get_summary() if latest_analysis else {}
        return render_template(
            "organization/dashboard.html",
            analysis=latest_analysis,
            summary=summary,
        )

    @app.route("/organization/upload", methods=["GET", "POST"])
    @organization_required
    def organization_upload():
        org_id = session["org_id"]

        if request.method == "POST":
            # Check if user clicked "Load Demo Dataset"
            if request.form.get("action") == "load_demo":
                demo_path = app.config["DATA_FOLDER"] / "demo_activity_data.csv"
                if not demo_path.exists():
                    flash("Demo dataset file is currently unavailable.", "danger")
                    return redirect(url_for("organization_upload"))

                df = pd.read_csv(demo_path)
                save_filename = f"demo_activity_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                saved_filepath = app.config["UPLOAD_FOLDER"] / save_filename
                df.to_csv(saved_filepath, index=False)

                dataset = Dataset(
                    organization_id=org_id,
                    filename="Demo Dataset (Academic Sample)",
                    filepath=str(saved_filepath),
                    row_count=len(df),
                    status="uploaded",
                    is_demo=True,
                )
                db.session.add(dataset)
                db.session.commit()

                flash("Demo dataset loaded successfully. Proceeding to Data Quality Preview.", "info")
                return redirect(url_for("organization_data_quality", dataset_id=dataset.id))

            # Standard File Upload
            if "file" not in request.files:
                flash("No file part provided in upload.", "danger")
                return redirect(url_for("organization_upload"))

            file = request.files["file"]
            if file.filename == "":
                flash("No file selected.", "danger")
                return redirect(url_for("organization_upload"))

            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in app.config["ALLOWED_EXTENSIONS"]:
                flash("Unsupported file format. Please upload CSV (.csv) or Excel (.xlsx).", "danger")
                return redirect(url_for("organization_upload"))

            # Save uploaded file safely
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            stored_name = f"{timestamp_str}_{filename}"
            target_path = app.config["UPLOAD_FOLDER"] / stored_name
            file.save(target_path)

            # Read dataset to verify parsing and row count
            try:
                if ext == "csv":
                    df = pd.read_csv(target_path)
                else:
                    df = pd.read_excel(target_path)
            except Exception as e:
                target_path.unlink(missing_ok=True)
                flash(f"Failed to parse uploaded file: {str(e)}", "danger")
                return redirect(url_for("organization_upload"))

            if df.empty:
                target_path.unlink(missing_ok=True)
                flash("Uploaded dataset is empty.", "danger")
                return redirect(url_for("organization_upload"))

            dataset = Dataset(
                organization_id=org_id,
                filename=filename,
                filepath=str(target_path),
                row_count=len(df),
                status="uploaded",
                is_demo=False,
            )
            db.session.add(dataset)
            db.session.commit()

            flash(f"File '{filename}' ({len(df)} rows) uploaded successfully.", "success")
            return redirect(url_for("organization_data_quality", dataset_id=dataset.id))

        # GET
        recent_datasets = (
            Dataset.query.filter_by(organization_id=org_id)
            .order_by(Dataset.uploaded_at.desc())
            .limit(5)
            .all()
        )
        return render_template("organization/upload.html", recent_datasets=recent_datasets)

    @app.route("/organization/data-quality/<int:dataset_id>", methods=["GET", "POST"])
    @organization_required
    def organization_data_quality(dataset_id):
        org_id = session["org_id"]
        dataset = Dataset.query.filter_by(id=dataset_id, organization_id=org_id).first_or_404()

        filepath = Path(dataset.filepath)
        if not filepath.exists():
            flash("Dataset source file was not found on server.", "danger")
            return redirect(url_for("organization_upload"))

        # Load file
        ext = filepath.suffix.lower().replace(".", "")
        df = pd.read_csv(filepath) if ext == "csv" else pd.read_excel(filepath)

        # Detect columns
        detected_mapping, unmapped = data_cleaning.detect_column_mappings(df.columns.tolist())
        is_valid, missing_cols, _ = data_cleaning.validate_columns(df, detected_mapping)

        # Audit previews
        _, duplicates_count = data_cleaning.detect_duplicates(df)
        missing_values_count = int(df.isna().sum().sum())

        if request.method == "POST":
            # Collect any manual mapping overrides
            manual_mapping = {}
            for std_col in data_cleaning.REQUIRED_ACTIVITY_COLUMNS + ["department", "employee_id", "meeting_hours"]:
                uploaded_val = request.form.get(f"map_{std_col}")
                if uploaded_val and uploaded_val in df.columns:
                    manual_mapping[std_col] = uploaded_val

            effective_mapping = manual_mapping if manual_mapping else detected_mapping

            # Execute non-destructive cleaning pipeline
            cleaned_df, cleaning_report = data_cleaning.clean_dataset(df, effective_mapping)

            # Execute vectorized carbon calculations
            calc_df = analysis_module.calculate_footprint_dataframe(cleaned_df)

            # Perform aggregations
            analysis_summary = analysis_module.perform_aggregations(calc_df)
            analysis_summary["cleaning_report"] = cleaning_report

            # Save clean and calculated datasets to disk for exports
            cleaned_path = app.config["EXPORTS_FOLDER"] / f"cleaned_dataset_{dataset.id}.csv"
            calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{dataset.id}.csv"
            cleaned_df.to_csv(cleaned_path, index=False)
            calc_df.to_csv(calc_path, index=False)

            # Persist Analysis in DB
            new_analysis = Analysis(
                organization_id=org_id,
                dataset_id=dataset.id,
                total_energy_kwh=analysis_summary["total_energy_kwh"],
                total_co2e_kg=analysis_summary["total_co2e_kg"],
                highest_impact_activity=analysis_summary["highest_impact_activity"],
                records_count=analysis_summary["record_count"],
                is_demo=dataset.is_demo,
                summary_json=json.dumps(analysis_summary),
            )
            db.session.add(new_analysis)
            db.session.flush()

            # Record activities
            for act_name, data in analysis_summary["activities"].items():
                db.session.add(
                    AnalysisActivity(
                        analysis_id=new_analysis.id,
                        activity_name=act_name,
                        energy_kwh=data.get("energy_kwh", 0.0),
                        co2e_kg=data.get("co2e_kg", 0.0),
                        percentage=data.get("percentage", 0.0),
                    )
                )

            # Record departments
            for dept in analysis_summary["departments"]:
                db.session.add(
                    AnalysisDepartment(
                        analysis_id=new_analysis.id,
                        department_name=dept["department"],
                        records_count=dept["records"],
                        energy_kwh=dept["energy_kwh"],
                        co2e_kg=dept["co2e_kg"],
                        percentage=dept["percentage"],
                    )
                )

            dataset.status = "analyzed"
            db.session.commit()

            # Generate publication charts
            chart_files = viz_module.generate_all_analysis_charts(
                new_analysis.id,
                analysis_summary,
                calc_df,
                app.config["CHARTS_FOLDER"],
            )
            analysis_summary["charts"] = chart_files
            new_analysis.summary_json = json.dumps(analysis_summary)
            db.session.commit()

            flash("Dataset successfully cleaned, standardized, and analyzed.", "success")
            return redirect(url_for("organization_analysis", analysis_id=new_analysis.id))

        # GET: Display Preview Table (first 15 rows)
        preview_rows = df.head(15).to_dict(orient="records")
        preview_cols = df.columns.tolist()

        return render_template(
            "organization/data_quality.html",
            dataset=dataset,
            preview_rows=preview_rows,
            preview_cols=preview_cols,
            detected_mapping=detected_mapping,
            unmapped=unmapped,
            is_valid=is_valid,
            missing_cols=missing_cols,
            duplicates_count=duplicates_count,
            missing_values_count=missing_values_count,
            required_cols=data_cleaning.REQUIRED_ACTIVITY_COLUMNS,
        )

    @app.route("/organization/analysis")
    @app.route("/organization/analysis/<int:analysis_id>")
    @organization_required
    def organization_analysis(analysis_id=None):
        org_id = session["org_id"]
        if analysis_id:
            analysis_obj = Analysis.query.filter_by(id=analysis_id, organization_id=org_id).first_or_404()
        else:
            analysis_obj = (
                Analysis.query.filter_by(organization_id=org_id)
                .order_by(Analysis.created_at.desc())
                .first()
            )

        if not analysis_obj:
            flash("No dataset has been analyzed yet. Please upload a dataset first.", "info")
            return redirect(url_for("organization_upload"))

        summary = analysis_obj.get_summary()

        # Load calculated dataset for descriptive statistics & ML evaluation
        calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
        eda_data = {}
        ml_data = {}
        if calc_path.exists():
            calc_df = pd.read_csv(calc_path)
            eda_data = analysis_module.compute_eda_summary(calc_df)
            ml_data = analysis_module.train_experimental_regression(calc_df)

        return render_template(
            "organization/analysis.html",
            analysis=analysis_obj,
            summary=summary,
            eda=eda_data,
            ml=ml_data,
        )

    @app.route("/organization/departments")
    @app.route("/organization/departments/<int:analysis_id>")
    @organization_required
    def organization_departments(analysis_id=None):
        org_id = session["org_id"]
        if analysis_id:
            analysis_obj = Analysis.query.filter_by(id=analysis_id, organization_id=org_id).first_or_404()
        else:
            analysis_obj = (
                Analysis.query.filter_by(organization_id=org_id)
                .order_by(Analysis.created_at.desc())
                .first()
            )

        if not analysis_obj:
            flash("No analysis available.", "info")
            return redirect(url_for("organization_upload"))

        summary = analysis_obj.get_summary()
        return render_template(
            "organization/departments.html",
            analysis=analysis_obj,
            departments=summary.get("departments", []),
            summary=summary,
        )

    @app.route("/organization/insights")
    @app.route("/organization/insights/<int:analysis_id>")
    @organization_required
    def organization_insights(analysis_id=None):
        org_id = session["org_id"]
        if analysis_id:
            analysis_obj = Analysis.query.filter_by(id=analysis_id, organization_id=org_id).first_or_404()
        else:
            analysis_obj = (
                Analysis.query.filter_by(organization_id=org_id)
                .order_by(Analysis.created_at.desc())
                .first()
            )

        if not analysis_obj:
            flash("No analysis available.", "info")
            return redirect(url_for("organization_upload"))

        summary = analysis_obj.get_summary()
        calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
        calc_df = pd.read_csv(calc_path) if calc_path.exists() else pd.DataFrame()

        insights = rec_module.generate_organization_insights(summary, calc_df)

        return render_template(
            "organization/insights.html",
            analysis=analysis_obj,
            insights=insights,
            summary=summary,
        )

    @app.route("/organization/what-if", methods=["GET", "POST"])
    @organization_required
    def organization_what_if():
        org_id = session["org_id"]
        analysis_obj = (
            Analysis.query.filter_by(organization_id=org_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )

        if not analysis_obj:
            flash("Please analyze an activity dataset prior to simulating reduction scenarios.", "info")
            return redirect(url_for("organization_upload"))

        calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
        calc_df = pd.read_csv(calc_path) if calc_path.exists() else pd.DataFrame()

        # Compute baselines
        baseline_inputs = {
            "laptop_hours": float(calc_df["laptop_hours"].sum()) if not calc_df.empty else 0.0,
            "smartphone_hours": float(calc_df["smartphone_hours"].sum()) if not calc_df.empty else 0.0,
            "streaming_hours": float(calc_df["streaming_hours"].sum()) if not calc_df.empty else 0.0,
            "emails": float(calc_df["emails"].sum()) if not calc_df.empty else 0.0,
            "ai_queries": float(calc_df["ai_queries"].sum()) if not calc_df.empty else 0.0,
        }

        laptop_red = float(request.form.get("laptop_reduction", 10) if request.method == "POST" else 10)
        streaming_red = float(request.form.get("streaming_reduction", 20) if request.method == "POST" else 20)
        ai_red = float(request.form.get("ai_reduction", 15) if request.method == "POST" else 15)
        phone_red = float(request.form.get("phone_reduction", 5) if request.method == "POST" else 5)
        email_red = float(request.form.get("email_reduction", 10) if request.method == "POST" else 10)

        simulation = carbon_engine.calculate_reduction_potential(
            baseline_inputs,
            laptop_reduction_pct=laptop_red,
            streaming_reduction_pct=streaming_red,
            ai_reduction_pct=ai_red,
            smartphone_reduction_pct=phone_red,
            email_reduction_pct=email_red,
        )

        return render_template(
            "organization/what_if.html",
            analysis=analysis_obj,
            sim=simulation,
            laptop_red=laptop_red,
            streaming_red=streaming_red,
            ai_red=ai_red,
            phone_red=phone_red,
            email_red=email_red,
        )

    @app.route("/organization/reports")
    @app.route("/organization/reports/<int:analysis_id>")
    @organization_required
    def organization_reports(analysis_id=None):
        org_id = session["org_id"]
        if analysis_id:
            analysis_obj = Analysis.query.filter_by(id=analysis_id, organization_id=org_id).first_or_404()
        else:
            analysis_obj = (
                Analysis.query.filter_by(organization_id=org_id)
                .order_by(Analysis.created_at.desc())
                .first()
            )

        if not analysis_obj:
            flash("No analysis reports available.", "info")
            return redirect(url_for("organization_upload"))

        summary = analysis_obj.get_summary()
        calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
        calc_df = pd.read_csv(calc_path) if calc_path.exists() else pd.DataFrame()
        insights = rec_module.generate_organization_insights(summary, calc_df)

        return render_template(
            "organization/reports.html",
            analysis=analysis_obj,
            summary=summary,
            insights=insights,
        )

    @app.route("/organization/export/<export_type>/<int:analysis_id>")
    @organization_required
    def organization_export(export_type, analysis_id):
        org_id = session["org_id"]
        analysis_obj = Analysis.query.filter_by(id=analysis_id, organization_id=org_id).first_or_404()
        summary = analysis_obj.get_summary()

        if export_type == "cleaned":
            file_path = app.config["EXPORTS_FOLDER"] / f"cleaned_dataset_{analysis_obj.dataset_id}.csv"
            if not file_path.exists():
                abort(404)
            return send_file(file_path, as_attachment=True, download_name=f"carbonlens_cleaned_{analysis_obj.id}.csv", mimetype="text/csv")

        elif export_type == "calculated":
            file_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
            if not file_path.exists():
                abort(404)
            return send_file(file_path, as_attachment=True, download_name=f"carbonlens_calculated_{analysis_obj.id}.csv", mimetype="text/csv")

        elif export_type == "activities":
            out_file = app.config["EXPORTS_FOLDER"] / f"activity_summary_{analysis_obj.id}.csv"
            report_generator.export_activity_summary_csv(summary, out_file)
            return send_file(out_file, as_attachment=True, download_name=f"carbonlens_activities_{analysis_obj.id}.csv", mimetype="text/csv")

        elif export_type == "departments":
            out_file = app.config["EXPORTS_FOLDER"] / f"department_summary_{analysis_obj.id}.csv"
            report_generator.export_department_summary_csv(summary, out_file)
            return send_file(out_file, as_attachment=True, download_name=f"carbonlens_departments_{analysis_obj.id}.csv", mimetype="text/csv")

        elif export_type == "pdf":
            calc_path = app.config["EXPORTS_FOLDER"] / f"calculated_dataset_{analysis_obj.dataset_id}.csv"
            calc_df = pd.read_csv(calc_path) if calc_path.exists() else pd.DataFrame()
            insights = rec_module.generate_organization_insights(summary, calc_df)

            pdf_path = app.config["EXPORTS_FOLDER"] / f"carbonlens_report_{analysis_obj.id}.pdf"
            report_generator.generate_pdf_report(
                organization_name=session.get("org_name", "Organization"),
                dataset_name=analysis_obj.dataset.filename,
                analysis_summary=summary,
                insights=insights,
                output_path=pdf_path,
            )
            return send_file(pdf_path, as_attachment=True, download_name=f"carbonlens_report_{analysis_obj.id}.pdf")

        else:
            abort(400)

    # ---------------------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash("The uploaded file exceeds the 16 MB maximum size limit.", "danger")
        return redirect(request.referrer or url_for("index")), 413

    return app


if __name__ == "__main__":
    application = create_app("development")
    print("=================================================================")
    print(" CarbonLens — Digital Carbon Footprint Analytics Platform")
    print(" Local development server running at: http://127.0.0.1:5000")
    print("=================================================================")
    application.run(host="127.0.0.1", port=5000, debug=True)
