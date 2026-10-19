"""CarbonLens — Integrated Analytics & Exploratory Data Analysis (EDA) Module.

Provides comprehensive, academic-grade dataset exploration, Matplotlib/Seaborn visualizations,
interactive Plotly and Bokeh charts, univariate/bivariate/multivariate EDA, Random Forest
feature importance, PCA dimensionality reduction, and custom CSV upload validation.

ALL CHARTS ARE RENDERED IN MEMORY (base64 / JSON) with ZERO DISK WRITES for full Vercel safety.
"""

import io
import base64
import uuid
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import plotly.express as px
import plotly.io as pio

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool, ColumnDataSource

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

eda_bp = Blueprint("eda", __name__, url_prefix="/analytics")

# In-memory transient storage for user-uploaded CSVs (keyed by session token, zero disk writes)
CUSTOM_DATASETS: Dict[str, Dict[str, Any]] = {}

# Available Color Palettes and Styling Themes
THEMES = {
    "forest-lab": ["#1B4332", "#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2"],
    "viridis": ["#440154", "#414487", "#2a788e", "#22a884", "#7ad151", "#fde725"],
    "plasma": ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
    "mako": ["#0b0405", "#35264c", "#475c87", "#49969f", "#65c996", "#def5aa"],
    "coolwarm": ["#3b4cc0", "#6788ee", "#9bc4f5", "#f49a7b", "#e05844", "#b40426"],
    "crest": ["#2c5985", "#387a9b", "#4b9c9f", "#6cb896", "#99cf88", "#d1e37f"],
    "Set2": ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f"],
}


def apply_theme_palette(palette_name: str = "forest-lab") -> List[str]:
    """Configure matplotlib and seaborn styling with selected palette."""
    palette = THEMES.get(palette_name, THEMES["forest-lab"])
    plt.rcParams.update({
        "figure.facecolor": "#FBFBFA",
        "axes.facecolor": "#FBFBFA",
        "axes.edgecolor": "#CCCCCC",
        "axes.labelcolor": "#212529",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
        "grid.color": "#E9ECEF",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
        "font.family": "sans-serif",
        "font.size": 10.0,
    })
    sns.set_palette(palette)
    return palette


def fig_to_base64(fig) -> str:
    """Render a Matplotlib figure strictly in memory to a base64 encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=140)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def get_iris_dataframe() -> pd.DataFrame:
    """Load standard academic Iris flower dataset into standardized Pandas DataFrame."""
    iris = load_iris(as_frame=True)
    df = iris.frame.copy()
    # Normalize column names for clear UI presentation
    df.columns = [
        "sepal_length",
        "sepal_width",
        "petal_length",
        "petal_width",
        "target",
    ]
    df["species"] = iris.target.map(lambda i: iris.target_names[i])
    return df


def get_active_dataset() -> Tuple[pd.DataFrame, str, bool]:
    """Retrieve active dataset for current user: custom uploaded or default Iris."""
    token = session.get("eda_session_token")
    if token and token in CUSTOM_DATASETS:
        info = CUSTOM_DATASETS[token]
        return info["df"].copy(), info["name"], True
    return get_iris_dataframe(), "Iris Flower Dataset (Fisher, 1936)", False


# =============================================================================
# Matplotlib & Seaborn Chart Generators (Memory Safe)
# =============================================================================

def generate_line_chart(df: pd.DataFrame, x_col: str, y_col: str, palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Line Plot."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    sorted_df = df.sort_values(by=x_col)
    ax.plot(
        sorted_df[x_col].values,
        sorted_df[y_col].values,
        color=palette[0],
        linewidth=2.0,
        marker="o",
        markersize=4,
        markerfacecolor=palette[1 % len(palette)],
        alpha=0.9,
    )
    ax.set_title(f"Line Plot: {y_col} vs {x_col}", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(x_col, fontweight="600")
    ax.set_ylabel(y_col, fontweight="600")
    ax.grid(True, linestyle="--", alpha=0.6)

    corr = df[x_col].corr(df[y_col]) if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]) else 0
    interpretation = (
        f"Shows continuous trend progression of {y_col} across {x_col}. "
        f"Pearson correlation is r = {corr:.2f}, indicating a "
        f"{'strong positive' if corr > 0.6 else 'moderate' if corr > 0.2 else 'weak or negative'} association."
    )
    return fig_to_base64(fig), interpretation


def generate_bar_chart(df: pd.DataFrame, cat_col: str, num_col: str, palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Bar Chart."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    grouped = df.groupby(cat_col)[num_col].mean().reset_index()
    bars = ax.bar(
        grouped[cat_col].astype(str),
        grouped[num_col],
        color=palette[:len(grouped)],
        edgecolor="#143527",
        linewidth=0.8,
        width=0.55,
    )

    for bar in bars:
        h = bar.get_height()
        ax.annotate(
            f"{h:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#212529",
        )

    ax.set_title(f"Mean {num_col} by {cat_col}", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(cat_col, fontweight="600")
    ax.set_ylabel(f"Average {num_col}", fontweight="600")
    plt.xticks(rotation=15, ha="right")

    max_grp = grouped.loc[grouped[num_col].idxmax()]
    min_grp = grouped.loc[grouped[num_col].idxmin()]
    interpretation = (
        f"Category '{max_grp[cat_col]}' has the highest mean {num_col} ({max_grp[num_col]:.2f}), "
        f"while '{min_grp[cat_col]}' has the lowest ({min_grp[num_col]:.2f}), reflecting notable subgroup variance."
    )
    return fig_to_base64(fig), interpretation


def generate_hist_chart(df: pd.DataFrame, num_col: str, palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Histogram with KDE."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    sns.histplot(
        df[num_col].dropna(),
        kde=True,
        color=palette[1 % len(palette)],
        edgecolor=palette[0],
        alpha=0.65,
        ax=ax,
    )
    mean_val = df[num_col].mean()
    median_val = df[num_col].median()
    skew_val = df[num_col].skew()

    ax.axvline(mean_val, color="#B45309", linestyle="--", linewidth=1.5, label=f"Mean ({mean_val:.2f})")
    ax.axvline(median_val, color="#1B4332", linestyle="-", linewidth=1.5, label=f"Median ({median_val:.2f})")
    ax.legend(loc="upper right", frameon=True)

    ax.set_title(f"Distribution & Frequency: {num_col}", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(num_col, fontweight="600")
    ax.set_ylabel("Count / Frequency", fontweight="600")

    interpretation = (
        f"Mean value is {mean_val:.2f} with median {median_val:.2f}. "
        f"Sample skewness is {skew_val:.2f}, indicating a "
        f"{'right-skewed' if skew_val > 0.5 else 'left-skewed' if skew_val < -0.5 else 'symmetric'} distribution."
    )
    return fig_to_base64(fig), interpretation


def generate_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, hue_col: Optional[str], palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Scatter Plot."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    if hue_col and hue_col in df.columns:
        sns.scatterplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            palette=palette[:df[hue_col].nunique()],
            s=60,
            alpha=0.85,
            edgecolor="#FFFFFF",
            ax=ax,
        )
        ax.legend(title=hue_col, frameon=True)
    else:
        ax.scatter(df[x_col], df[y_col], color=palette[0], s=55, alpha=0.8, edgecolor="#FFFFFF")

    ax.set_title(f"Scatter Plot: {y_col} vs {x_col}", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(x_col, fontweight="600")
    ax.set_ylabel(y_col, fontweight="600")
    ax.grid(True, linestyle="--", alpha=0.6)

    corr = df[x_col].corr(df[y_col])
    interpretation = (
        f"Pearson correlation r = {corr:.2f}. "
        f"{'A prominent linear separation is visible across classes.' if hue_col else 'Data points show ' + ('positive' if corr > 0.3 else 'negative' if corr < -0.3 else 'moderate') + ' alignment.'}"
    )
    return fig_to_base64(fig), interpretation


def generate_pie_chart(df: pd.DataFrame, cat_col: str, palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Pie Chart."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))

    counts = df[cat_col].value_counts()
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=[str(l) for l in counts.index],
        autopct="%1.1f%%",
        startangle=140,
        colors=palette[:len(counts)],
        wedgeprops={"edgecolor": "#FFFFFF", "linewidth": 1.2},
    )
    for at in autotexts:
        at.set_color("#FFFFFF")
        at.set_fontweight("bold")
        at.set_fontsize(9)

    ax.set_title(f"Class Proportions ({cat_col})", fontweight="bold", color="#1B4332", pad=10)

    interpretation = (
        f"Dataset contains {len(counts)} distinct classes across {len(df)} total rows. "
        f"Top category '{counts.index[0]}' represents {counts.iloc[0]} records ({counts.iloc[0]/len(df)*100:.1f}%)."
    )
    return fig_to_base64(fig), interpretation


def generate_box_chart(df: pd.DataFrame, cat_col: str, num_col: str, palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Box Plot."""
    palette = apply_theme_palette(palette_name)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    sns.boxplot(
        data=df,
        x=cat_col,
        y=num_col,
        hue=cat_col,
        palette=palette[:df[cat_col].nunique()],
        legend=False,
        width=0.5,
        ax=ax,
    )
    ax.set_title(f"Boxplot: {num_col} by {cat_col}", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(cat_col, fontweight="600")
    ax.set_ylabel(num_col, fontweight="600")
    plt.xticks(rotation=15, ha="right")

    interpretation = (
        f"Illustrates the median, 25th-75th quartile dispersion (IQR), and outlier boundaries "
        f"for {num_col} stratified across {cat_col} groups."
    )
    return fig_to_base64(fig), interpretation


# =============================================================================
# Advanced EDA: Heatmap & Pair Plot (Memory Safe)
# =============================================================================

def generate_heatmap_chart(df: pd.DataFrame, palette_name: str) -> Tuple[str, str]:
    """Generate correlation heatmap for numeric features."""
    apply_theme_palette(palette_name)
    num_df = df.select_dtypes(include=[np.number])
    if "target" in num_df.columns:
        num_df = num_df.drop(columns=["target"])

    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    corr = num_df.corr()
    cmap = "Greens" if palette_name == "forest-lab" else "viridis"

    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        linewidths=1.0,
        square=True,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )
    ax.set_title("Feature Correlation Matrix (Pearson)", fontweight="bold", color="#1B4332", pad=12)

    # Detect strongest correlation
    unstacked = corr.abs().unstack()
    unstacked = unstacked[unstacked < 0.9999].sort_values(ascending=False)
    if not unstacked.empty:
        feat1, feat2 = unstacked.index[0]
        actual_r = corr.loc[feat1, feat2]
        interpretation = (
            f"Strongest pairwise correlation is between '{feat1}' and '{feat2}' (r = {actual_r:.2f}), "
            f"indicating substantial shared variance."
        )
    else:
        interpretation = "Correlation heatmap computed across all continuous variables."

    return fig_to_base64(fig), interpretation


def generate_pairplot_chart(df: pd.DataFrame, hue_col: Optional[str], palette_name: str) -> Tuple[str, str]:
    """Generate in-memory Seaborn Pairplot."""
    palette = apply_theme_palette(palette_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "target" in num_cols:
        num_cols.remove("target")

    plot_df = df[num_cols + ([hue_col] if hue_col and hue_col in df.columns else [])]
    g = sns.pairplot(
        plot_df,
        hue=hue_col if hue_col and hue_col in df.columns else None,
        palette=palette[:df[hue_col].nunique()] if hue_col and hue_col in df.columns else None,
        corner=True,
        diag_kind="kde",
    )
    g.fig.suptitle("Multivariate Pair Plot & Distributions", y=1.02, fontweight="bold", color="#1B4332")

    buf = io.BytesIO()
    g.fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(g.fig)

    interpretation = (
        "Multi-panel pair plot visualizes pairwise bivariate scatter distributions along the lower triangle "
        "and univariate kernel density estimations along the diagonal."
    )
    return encoded, interpretation


# =============================================================================
# Interactive Visualizations: Plotly & Bokeh
# =============================================================================

def generate_interactive_plotly(df: pd.DataFrame, x_col: str, y_col: str, hue_col: Optional[str]) -> str:
    """Generate an interactive Plotly scatter plot with zoom, pan, hover tooltips."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=hue_col if hue_col and hue_col in df.columns else None,
        title=f"Interactive Plotly: {y_col} vs {x_col}",
        template="plotly_white",
        hover_data=df.columns.tolist()[:6],
    )
    fig.update_layout(
        font=dict(family="sans-serif", size=12),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def generate_interactive_bokeh(df: pd.DataFrame, x_col: str, y_col: str, hue_col: Optional[str]) -> Tuple[str, str]:
    """Generate interactive Bokeh chart with HoverTool, pan, wheel_zoom, and reset."""
    source_df = df.copy()
    source = ColumnDataSource(source_df)

    p = figure(
        title=f"Interactive Bokeh: {y_col} vs {x_col}",
        width=780,
        height=400,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        background_fill_color="#FBFBFA",
        border_fill_color="#FFFFFF",
    )

    p.scatter(
        x=x_col,
        y=y_col,
        source=source,
        size=9,
        color="#2D6A4F",
        alpha=0.8,
        line_color="#FFFFFF",
    )

    tooltips = [(x_col, f"@{{{x_col}}}"), (y_col, f"@{{{y_col}}}")]
    if hue_col and hue_col in df.columns:
        tooltips.insert(0, (hue_col, f"@{{{hue_col}}}"))

    p.add_tools(HoverTool(tooltips=tooltips))
    p.xaxis.axis_label = x_col
    p.yaxis.axis_label = y_col

    script, div = components(p)
    return script, div


# =============================================================================
# Advanced Machine Learning: Random Forest & PCA
# =============================================================================

def compute_random_forest_importance(df: pd.DataFrame, target_col: str, palette_name: str) -> Dict[str, Any]:
    """Train Random Forest classifier, evaluate on holdout test set, and extract feature importances."""
    palette = apply_theme_palette(palette_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in num_cols:
        num_cols.remove(target_col)

    if len(num_cols) < 2 or df[target_col].nunique() < 2 or len(df) < 15:
        return {"available": False, "reason": "Insufficient features or observations for Random Forest classification."}

    X = df[num_cols].fillna(df[num_cols].median())
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    importances = dict(zip(X.columns, [float(v) for v in rf.feature_importances_]))

    # Render bar chart
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    sorted_feats = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    f_names = [f[0] for f in sorted_feats]
    f_scores = [f[1] for f in sorted_feats]

    bars = ax.barh(f_names[::-1], f_scores[::-1], color=palette[:len(f_names)], edgecolor="#143527", height=0.55)
    for bar in bars:
        w = bar.get_width()
        ax.annotate(
            f"{w:.3f}",
            xy=(w, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#212529",
        )

    ax.set_title("Random Forest Gini Feature Importances", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel("Mean Decrease in Impurity (Gini)", fontweight="600")
    top_feature = f_names[0]
    top_weight = f_scores[0] * 100

    interpretation = (
        f"Random Forest model trained with 75/25 split achieved {acc * 100:.1f}% test accuracy. "
        f"Top discriminator is '{top_feature}' contributing {top_weight:.1f}% of total classification weight."
    )

    return {
        "available": True,
        "accuracy": f"{acc * 100:.1f}%",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "importances": importances,
        "chart_b64": fig_to_base64(fig),
        "interpretation": interpretation,
    }


def compute_pca_analysis(df: pd.DataFrame, hue_col: Optional[str], palette_name: str) -> Dict[str, Any]:
    """Execute standardized Principal Component Analysis (PCA) with explained variance."""
    palette = apply_theme_palette(palette_name)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "target" in num_cols:
        num_cols.remove("target")

    if len(num_cols) < 2 or len(df) < 10:
        return {"available": False, "reason": "At least 2 numeric features required for PCA projection."}

    X = df[num_cols].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    coords = pca.fit_transform(X_scaled)
    ev = pca.explained_variance_ratio_

    pca_df = pd.DataFrame(coords, columns=["PC1", "PC2"])
    if hue_col and hue_col in df.columns:
        pca_df[hue_col] = df.loc[X.index, hue_col].values

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    if hue_col and hue_col in pca_df.columns:
        sns.scatterplot(
            data=pca_df,
            x="PC1",
            y="PC2",
            hue=hue_col,
            palette=palette[:pca_df[hue_col].nunique()],
            s=65,
            alpha=0.85,
            edgecolor="#FFFFFF",
            ax=ax,
        )
        ax.legend(title=hue_col, frameon=True)
    else:
        ax.scatter(pca_df["PC1"], pca_df["PC2"], color=palette[0], s=60, alpha=0.8, edgecolor="#FFFFFF")

    ax.set_title("Standardized PCA 2D Dimensionality Projection", fontweight="bold", color="#1B4332", pad=10)
    ax.set_xlabel(f"Principal Component 1 ({ev[0] * 100:.1f}% Variance)", fontweight="600")
    ax.set_ylabel(f"Principal Component 2 ({ev[1] * 100:.1f}% Variance)", fontweight="600")
    ax.grid(True, linestyle="--", alpha=0.6)

    total_ev = (ev[0] + ev[1]) * 100
    interpretation = (
        f"PC1 explains {ev[0] * 100:.1f}% and PC2 explains {ev[1] * 100:.1f}% of continuous variance "
        f"({total_ev:.1f}% cumulative). The 2D projection reveals clear unsupervised separation across clusters."
    )

    return {
        "available": True,
        "ev1": f"{ev[0] * 100:.1f}%",
        "ev2": f"{ev[1] * 100:.1f}%",
        "total_ev": f"{total_ev:.1f}%",
        "chart_b64": fig_to_base64(fig),
        "interpretation": interpretation,
    }


# =============================================================================
# Blueprint Route Controller
# =============================================================================

@eda_bp.route("", methods=["GET"])
@eda_bp.route("/", methods=["GET"])
def eda_index():
    """Main Analytics & Exploratory Data Analysis studio route."""
    df, dataset_name, is_custom = get_active_dataset()
    palette_name = request.args.get("palette", "forest-lab")
    if palette_name not in THEMES:
        palette_name = "forest-lab"

    # Numeric & Categorical Columns
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "target" in num_cols:
        num_cols.remove("target")
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    if not cat_cols and "species" in df.columns:
        cat_cols = ["species"]

    # Parameter selection
    line_x = request.args.get("line_x", num_cols[0] if num_cols else "")
    line_y = request.args.get("line_y", num_cols[1] if len(num_cols) > 1 else line_x)
    bar_cat = request.args.get("bar_cat", cat_cols[0] if cat_cols else "")
    bar_num = request.args.get("bar_num", num_cols[0] if num_cols else "")
    hist_col = request.args.get("hist_col", num_cols[0] if num_cols else "")
    scatter_x = request.args.get("scatter_x", num_cols[0] if num_cols else "")
    scatter_y = request.args.get("scatter_y", num_cols[1] if len(num_cols) > 1 else scatter_x)
    scatter_hue = request.args.get("scatter_hue", cat_cols[0] if cat_cols else None)
    pie_cat = request.args.get("pie_cat", cat_cols[0] if cat_cols else "")
    box_cat = request.args.get("box_cat", cat_cols[0] if cat_cols else "")
    box_num = request.args.get("box_num", num_cols[0] if num_cols else "")

    # 1. Dataset Exploration Summary
    preview_rows = df.head(10).to_dict(orient="records")
    shape = df.shape
    col_summary = []
    for col in df.columns:
        col_summary.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
        })

    describe_dict = df.describe().to_dict()

    # 2. Matplotlib / Seaborn Charts (Generated strictly in memory to base64)
    line_b64, line_interp = generate_line_chart(df, line_x, line_y, palette_name) if line_x and line_y else ("", "")
    bar_b64, bar_interp = generate_bar_chart(df, bar_cat, bar_num, palette_name) if bar_cat and bar_num else ("", "")
    hist_b64, hist_interp = generate_hist_chart(df, hist_col, palette_name) if hist_col else ("", "")
    scatter_b64, scatter_interp = generate_scatter_chart(df, scatter_x, scatter_y, scatter_hue, palette_name) if scatter_x and scatter_y else ("", "")
    pie_b64, pie_interp = generate_pie_chart(df, pie_cat, palette_name) if pie_cat else ("", "")
    box_b64, box_interp = generate_box_chart(df, box_cat, box_num, palette_name) if box_cat and box_num else ("", "")

    # 3. Statistical EDA: Heatmap & Pairplot
    heatmap_b64, heatmap_interp = generate_heatmap_chart(df, palette_name) if len(num_cols) >= 2 else ("", "")
    pairplot_b64, pairplot_interp = generate_pairplot_chart(df, scatter_hue, palette_name) if len(num_cols) >= 2 else ("", "")

    # 4. Interactive Visualizations (Plotly & Bokeh)
    plotly_div = generate_interactive_plotly(df, scatter_x, scatter_y, scatter_hue) if scatter_x and scatter_y else ""
    bokeh_script, bokeh_div = generate_interactive_bokeh(df, scatter_x, scatter_y, scatter_hue) if scatter_x and scatter_y else ("", "")

    # 5. Advanced Machine Learning
    target_candidate = cat_cols[0] if cat_cols else ("target" if "target" in df.columns else None)
    rf_data = compute_random_forest_importance(df, target_candidate, palette_name) if target_candidate else {"available": False, "reason": "No discrete classification target identified."}
    pca_data = compute_pca_analysis(df, scatter_hue, palette_name)

    return render_template(
        "eda/index.html",
        dataset_name=dataset_name,
        is_custom=is_custom,
        shape=shape,
        preview_rows=preview_rows,
        col_summary=col_summary,
        describe_dict=describe_dict,
        num_cols=num_cols,
        cat_cols=cat_cols,
        selected_palette=palette_name,
        available_palettes=list(THEMES.keys()),
        # Chart data
        line_b64=line_b64,
        line_interp=line_interp,
        line_x=line_x,
        line_y=line_y,
        bar_b64=bar_b64,
        bar_interp=bar_interp,
        bar_cat=bar_cat,
        bar_num=bar_num,
        hist_b64=hist_b64,
        hist_interp=hist_interp,
        hist_col=hist_col,
        scatter_b64=scatter_b64,
        scatter_interp=scatter_interp,
        scatter_x=scatter_x,
        scatter_y=scatter_y,
        scatter_hue=scatter_hue,
        pie_b64=pie_b64,
        pie_interp=pie_interp,
        pie_cat=pie_cat,
        box_b64=box_b64,
        box_interp=box_interp,
        box_cat=box_cat,
        box_num=box_num,
        heatmap_b64=heatmap_b64,
        heatmap_interp=heatmap_interp,
        pairplot_b64=pairplot_b64,
        pairplot_interp=pairplot_interp,
        plotly_div=plotly_div,
        bokeh_script=bokeh_script,
        bokeh_div=bokeh_div,
        rf_data=rf_data,
        pca_data=pca_data,
    )


@eda_bp.route("/upload", methods=["POST"])
def eda_upload():
    """Upload custom CSV with in-memory parsing, strict validation, and friendly error feedback."""
    if "file" not in request.files:
        flash("No file part attached in request.", "danger")
        return redirect(url_for("eda.eda_index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No CSV file selected for upload.", "danger")
        return redirect(url_for("eda.eda_index"))

    if not file.filename.lower().endswith(".csv"):
        flash("Unsupported format: Only comma-separated (.csv) files are permitted in EDA Studio.", "danger")
        return redirect(url_for("eda.eda_index"))

    try:
        content = file.read().decode("utf-8", errors="replace")
        if not content.strip():
            flash("The uploaded CSV file is empty.", "danger")
            return redirect(url_for("eda.eda_index"))

        df = pd.read_csv(io.StringIO(content))
        if len(df) < 3:
            flash(f"Dataset too small ({len(df)} rows). A minimum of 3 rows is required for statistical EDA.", "danger")
            return redirect(url_for("eda.eda_index"))

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            flash("Uploaded dataset contains no numeric columns. At least one numeric column is required for charts.", "danger")
            return redirect(url_for("eda.eda_index"))

        # Initialize session token if not present
        if "eda_session_token" not in session:
            session["eda_session_token"] = str(uuid.uuid4())

        token = session["eda_session_token"]
        CUSTOM_DATASETS[token] = {
            "df": df,
            "name": file.filename,
        }

        flash(f"Custom dataset '{file.filename}' ({len(df)} rows, {len(df.columns)} columns) parsed and activated successfully.", "success")
        return redirect(url_for("eda.eda_index"))

    except Exception as e:
        flash(f"Could not parse uploaded CSV: {str(e)}", "danger")
        return redirect(url_for("eda.eda_index"))


@eda_bp.route("/reset", methods=["POST"])
def eda_reset():
    """Reset active dataset back to standard Iris dataset."""
    token = session.get("eda_session_token")
    if token and token in CUSTOM_DATASETS:
        del CUSTOM_DATASETS[token]
    flash("Switched back to the default Fisher Iris dataset.", "info")
    return redirect(url_for("eda.eda_index"))
