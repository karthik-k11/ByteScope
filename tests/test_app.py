import io
import json
import sqlite3

from app import create_app


def _client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "history.sqlite3"),
        }
    )
    return app.test_client()


def test_upload_analysis_history_and_json_export(tmp_path):
    client = _client(tmp_path)
    response = client.post(
        "/analyze",
        data={"file": (io.BytesIO(b"%PDF-1.4\n%%EOF"), "notes.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"notes.pdf" in response.data
    assert b"PDF" in response.data
    assert b"Download JSON" in response.data

    history_response = client.get("/")
    assert b"Recent analyses" in history_response.data
    assert b"notes.pdf" in history_response.data

    with sqlite3.connect(tmp_path / "history.sqlite3") as connection:
        analysis_id = connection.execute(
            "SELECT id FROM analyses"
        ).fetchone()[0]

    export = client.get(f"/report/{analysis_id}.json")
    assert export.status_code == 200
    assert export.headers["Content-Type"].startswith("application/json")
    assert json.loads(export.data)["sha256"]
    assert "attachment" in export.headers["Content-Disposition"]


def test_extension_mismatch_is_visible(tmp_path):
    client = _client(tmp_path)
    response = client.post(
        "/analyze",
        data={"file": (io.BytesIO(b"%PDF-1.4\n%%EOF"), "picture.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Mismatch" in response.data


def test_compare_route_reports_identical_files(tmp_path):
    client = _client(tmp_path)
    response = client.post(
        "/compare",
        data={
            "first_file": (io.BytesIO(b"same"), "one.bin"),
            "second_file": (io.BytesIO(b"same"), "two.bin"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"byte-for-byte identical" in response.data


def test_missing_upload_and_unknown_report_are_reported(tmp_path):
    client = _client(tmp_path)

    assert client.post("/analyze").status_code == 400
    assert client.get("/report/not-a-report.json").status_code == 404


def test_empty_file_is_valid_and_oversized_request_is_rejected(tmp_path):
    client = _client(tmp_path)
    empty_response = client.post(
        "/analyze",
        data={"file": (io.BytesIO(b""), "empty.bin")},
        content_type="multipart/form-data",
    )
    assert empty_response.status_code == 200
    assert b"Empty file" in empty_response.data

    limited_client = create_app(
        {
            "TESTING": True,
            "MAX_CONTENT_LENGTH": 128,
            "DATABASE": str(tmp_path / "limited-history.sqlite3"),
        }
    ).test_client()
    large_response = limited_client.post(
        "/analyze",
        data={"file": (io.BytesIO(b"x" * 512), "large.bin")},
        content_type="multipart/form-data",
    )
    assert large_response.status_code == 413
