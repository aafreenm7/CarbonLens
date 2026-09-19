"""CarbonLens Report Generator & Multi-Format Exporter.

Provides verified CSV dataset exports via Pandas and formal academic PDF
executive reports via ReportLab.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd


def export_cleaned_dataset_csv(cleaned_df: pd.DataFrame, output_path: Path) -> Path:
    """Export the validated and cleaned activity dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    return output_path


def export_calculated_dataset_csv(calc_df: pd.DataFrame, output_path: Path) -> Path:
    """Export the dataset with full vectorized energy and emission calculations."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    calc_df.to_csv(output_path, index=False)
    return output_path


def export_activity_summary_csv(analysis_summary: Dict[str, Any], output_path: Path) -> Path:
    """Export the activity-level emissions and energy breakdown to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    activities = analysis_summary.get("activities", {})
    rows = []
    for name, data in activities.items():
        rows.append({
            "Activity": name,
            "Direct_Energy_kWh": data.get("energy_kwh", 0.0),
            "Estimated_CO2e_kg": data.get("co2e_kg", 0.0),
            "Contribution_Percentage": data.get("percentage", 0.0),
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return output_path


def export_department_summary_csv(analysis_summary: Dict[str, Any], output_path: Path) -> Path:
    """Export department breakdown to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    depts = analysis_summary.get("departments", [])
    df = pd.DataFrame(depts)
    df.to_csv(output_path, index=False)
    return output_path


def generate_pdf_report(
    organization_name: str,
    dataset_name: str,
    analysis_summary: Dict[str, Any],
    insights: List[Dict[str, Any]],
    output_path: Path,
) -> Path:
    """Generate a publication-grade academic PDF report using ReportLab.

    Contains genuine analysis metrics, activity tables, department stats,
    data-driven insights, methodology, and verified scientific references.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Custom Academic Styles
    primary_color = colors.HexColor("#1B4332")
    secondary_color = colors.HexColor("#2D6A4F")
    charcoal = colors.HexColor("#212529")
    offwhite = colors.HexColor("#F8F9FA")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        spaceAfter=15,
    )

    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=charcoal,
    )

    callout_style = ParagraphStyle(
        "ReportCallout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#495057"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("CARBONLENS — DIGITAL FOOTPRINT REPORT", title_style))
    story.append(
        Paragraph(
            f"Organization: <b>{organization_name}</b> &nbsp;|&nbsp; Dataset: <b>{dataset_name}</b> &nbsp;|&nbsp; Date: <b>{datetime.now().strftime('%d %B %Y')}</b>",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=15))

    # 2. Executive Summary Metrics Table
    story.append(Paragraph("1. Executive Summary", h2_style))
    total_co2 = analysis_summary.get("total_co2e_kg", 0.0)
    total_energy = analysis_summary.get("total_energy_kwh", 0.0)
    record_count = analysis_summary.get("record_count", 0)
    monthly_co2 = analysis_summary.get("monthly_co2e_kg", 0.0)
    yearly_co2 = analysis_summary.get("yearly_co2e_kg", 0.0)
    highest_act = analysis_summary.get("highest_impact_activity", "None")

    kpi_data = [
        [
            Paragraph("<b>Analyzed Records</b>", body_style),
            Paragraph(f"<b>{record_count}</b>", body_style),
            Paragraph("<b>Estimated Daily Energy</b>", body_style),
            Paragraph(f"<b>{total_energy:.2f} kWh</b>", body_style),
        ],
        [
            Paragraph("<b>Estimated Daily CO₂e</b>", body_style),
            Paragraph(f"<b>{total_co2:.2f} kg</b>", body_style),
            Paragraph("<b>Highest Impact Driver</b>", body_style),
            Paragraph(f"<b>{highest_act}</b>", body_style),
        ],
        [
            Paragraph("<b>Monthly Projection (30d)</b>", body_style),
            Paragraph(f"<b>{monthly_co2:.2f} kg</b>", body_style),
            Paragraph("<b>Yearly Projection (365d)</b>", body_style),
            Paragraph(f"<b>{yearly_co2:.2f} kg</b>", body_style),
        ],
    ]

    kpi_table = Table(kpi_data, colWidths=[140, 110, 140, 110])
    kpi_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), offwhite),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E9ECEF")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 3. Activity Breakdown Table
    story.append(Paragraph("2. Activity-Level Carbon & Energy Breakdown", h2_style))
    act_data_rows = [["Activity", "Direct Energy (kWh)", "Emissions (kg CO₂e)", "Contribution (%)"]]
    for act_name, data in analysis_summary.get("activities", {}).items():
        act_data_rows.append([
            act_name,
            f"{data.get('energy_kwh', 0.0):.2f}",
            f"{data.get('co2e_kg', 0.0):.2f}",
            f"{data.get('percentage', 0.0):.1f}%",
        ])

    act_table = Table(act_data_rows, colWidths=[180, 110, 110, 100])
    act_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, offwhite]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(act_table)
    story.append(Spacer(1, 12))

    # 4. Department Breakdown Table
    story.append(Paragraph("3. Departmental Allocation", h2_style))
    dept_data_rows = [["Department", "Employees", "Total Energy (kWh)", "Emissions (kg)", "Share (%)"]]
    for d in analysis_summary.get("departments", [])[:8]:  # Top 8
        dept_data_rows.append([
            d.get("department", "Unknown"),
            str(d.get("records", 0)),
            f"{d.get('energy_kwh', 0.0):.2f}",
            f"{d.get('co2e_kg', 0.0):.2f}",
            f"{d.get('percentage', 0.0):.1f}%",
        ])

    dept_table = Table(dept_data_rows, colWidths=[160, 70, 110, 80, 80])
    dept_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, offwhite]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(dept_table)
    story.append(Spacer(1, 12))

    # 5. Algorithmic Insights
    story.append(Paragraph("4. Key Data-Driven Insights & Reduction Strategies", h2_style))
    for ins in insights[:3]:
        story.append(Paragraph(f"<b>• {ins.get('title')}:</b> {ins.get('observation')}", body_style))
        story.append(Paragraph(f"&nbsp;&nbsp;<i>Action:</i> {ins.get('recommendation')}", callout_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # 6. Scientific Methodology & Emission Boundaries
    story.append(Paragraph("5. Scientific Methodology & System Boundaries", h2_style))
    story.append(
        Paragraph(
            "<b>Indian Grid Factor:</b> 0.710 kg CO₂e/kWh (Central Electricity Authority FY2024–25).<br/>"
            "<b>Equipment Power Assumptions:</b> Laptop active power = 50 W; Smartphone power = 2 W.<br/>"
            "<b>Video Streaming:</b> 36 g CO₂e/hour (IEA 2020 boundary: transmission, data centers, user display). "
            "<i>To prevent double-counting, display device electricity is not added to streaming emissions.</i><br/>"
            "<b>Generative AI Queries:</b> 0.31 Wh/query (Oviedo et al., Joule 2026).<br/>"
            "<b>Electronic Mail:</b> 0.3 g CO₂e/message (Updated Berners-Lee figures).",
            callout_style,
        )
    )
    story.append(Spacer(1, 8))

    # 7. Academic Limitations
    story.append(Paragraph("6. Academic Limitations", h2_style))
    story.append(
        Paragraph(
            "The CarbonLens result is an analytical estimate based on activity data and published/project "
            "modelling factors. It is not a direct physical measurement of electricity consumption. "
            "Actual emissions vary with device hardware efficiency, network topology, server load, and dynamic grid mix.",
            callout_style,
        )
    )

    doc.build(story)
    return output_path
