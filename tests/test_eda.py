import io
import pytest
from app import create_app
from database import db


@pytest.fixture
def client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_eda_index_default_iris_rendering(client):
    """Verify that Analytics / EDA Studio renders default Iris dataset and in-memory charts."""
    resp = client.get("/analytics")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # 1. Dataset exploration inspection
    assert "Iris Flower Dataset" in html or "Iris" in html
    assert "150 rows" in html
    assert "columns" in html
    assert "sepal_length" in html
    assert "petal_length" in html
    assert "species" in html
    assert "Descriptive Statistics" in html
    assert "COUNT" in html
    assert "MEAN" in html

    # 2. In-memory base64 chart delivery
    assert "data:image/png;base64," in html

    # 3. Interactive visualizations (Plotly & Bokeh CDN integration)
    assert "cdn.plot.ly" in html
    assert "cdn.bokeh.org" in html
    assert "Plotly" in html
    assert "Bokeh" in html

    # 4. Statistical EDA: Heatmap & Pairplot
    assert "Pearson Correlation Heatmap" in html
    assert "Multivariate Pair Plot" in html

    # 5. Advanced Machine Learning: Random Forest & PCA
    assert "Random Forest Feature Importance" in html
    assert "Principal Component Analysis" in html
    assert "PC1 Variance" in html
    assert "Model Holdout Accuracy" in html

    # 6. Data-driven interpretations present
    assert "Data-Driven Interpretation:" in html


def test_eda_theme_palette_switching(client):
    """Verify that dynamic palette switching works and renders cleanly."""
    for pal in ["viridis", "plasma", "coolwarm", "mako", "crest", "Set2"]:
        resp = client.get(f"/analytics?palette={pal}")
        assert resp.status_code == 200
        assert f'value="{pal}" selected' in resp.data.decode("utf-8")


def test_eda_custom_csv_upload_validation(client):
    """Verify strict validation and friendly error messages for CSV uploads."""
    # 1. Reject missing file
    resp_empty = client.post("/analytics/upload", data={}, follow_redirects=True)
    assert resp_empty.status_code == 200
    assert "No file part" in resp_empty.data.decode("utf-8") or "No CSV file" in resp_empty.data.decode("utf-8")

    # 2. Reject non-CSV format
    bad_format = (io.BytesIO(b"fake image data"), "test.jpg")
    resp_format = client.post(
        "/analytics/upload",
        data={"file": bad_format},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "Unsupported format" in resp_format.data.decode("utf-8")

    # 3. Reject empty CSV
    empty_csv = (io.BytesIO(b""), "empty.csv")
    resp_empty_csv = client.post(
        "/analytics/upload",
        data={"file": empty_csv},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "empty" in resp_empty_csv.data.decode("utf-8").lower()

    # 4. Reject CSV with < 3 rows
    small_csv_content = b"feature1,feature2\n10,20\n"
    small_csv = (io.BytesIO(small_csv_content), "small.csv")
    resp_small = client.post(
        "/analytics/upload",
        data={"file": small_csv},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "too small" in resp_small.data.decode("utf-8").lower()

    # 5. Reject CSV with no numeric columns
    text_csv_content = b"col1,col2\nalpha,beta\ngamma,delta\nepsilon,zeta\n"
    text_csv = (io.BytesIO(text_csv_content), "text_only.csv")
    resp_text = client.post(
        "/analytics/upload",
        data={"file": text_csv},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "no numeric columns" in resp_text.data.decode("utf-8").lower()

    # 6. Accept valid custom CSV
    valid_csv_content = (
        b"metric_a,metric_b,category\n"
        b"12.5,45.2,Alpha\n"
        b"14.1,48.0,Alpha\n"
        b"22.3,60.1,Beta\n"
        b"25.0,63.4,Beta\n"
        b"18.7,52.9,Gamma\n"
    )
    valid_csv = (io.BytesIO(valid_csv_content), "custom_experiment.csv")
    resp_valid = client.post(
        "/analytics/upload",
        data={"file": valid_csv},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp_valid.status_code == 200
    valid_html = resp_valid.data.decode("utf-8")
    assert "custom_experiment.csv" in valid_html
    assert "5 rows" in valid_html
    assert "metric_a" in valid_html

    # 7. Test Reset back to Iris
    resp_reset = client.post("/analytics/reset", follow_redirects=True)
    assert resp_reset.status_code == 200
    reset_html = resp_reset.data.decode("utf-8")
    assert "Switched back to the default Fisher Iris dataset" in reset_html
    assert "150 rows" in reset_html
