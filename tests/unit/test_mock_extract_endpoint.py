from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

_MINIMAL_PDF = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def test_extract_mock_pdf_returns_fixed_records_with_source_filename():
    response = client.post(
        "/extract/mock/pdf",
        files={"file": ("passport_1.pdf", _MINIMAL_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_file"] == "passport_1.pdf"
    assert len(data["records"]) >= 2
    assert any(r["date"] is None for r in data["records"])
    assert any(r["date"] is not None for r in data["records"])


def test_extract_mock_pdf_rejects_non_pdf_upload():
    response = client.post(
        "/extract/mock/pdf",
        files={"file": ("stamp.png", b"not a real png", "image/png")},
    )
    assert response.status_code == 400


def test_extract_mock_pdf_returns_chronologically_sorted_timeline():
    response = client.post(
        "/extract/mock/pdf",
        files={"file": ("passport_1.pdf", _MINIMAL_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    timeline = response.json()["timeline"]

    dates = [e["date"] for e in timeline["events"]]
    assert dates == sorted(dates)                    # ascending by date
    assert all(d is not None for d in dates)         # placeable events all dated
    assert len(timeline["undated"]) >= 1             # null-date record is not placed
    assert set(timeline["events"][0]) >= {"date", "country", "direction"}
