import logging
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from file_analyzer import analyze_file, compare_files
from history import get_analysis, list_analyses, save_analysis


MAX_UPLOAD_BYTES = 64 * 1024 * 1024
logger = logging.getLogger(__name__)


def _save_upload(upload, directory):
    safe_name = secure_filename(upload.filename or "")
    if not safe_name:
        raise ValueError("Choose a file with a valid filename.")
    destination = Path(directory) / f"upload{Path(safe_name).suffix[:20]}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    upload.save(destination)
    return destination, safe_name


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
        DATABASE=str(Path(app.instance_path) / "history.sqlite3"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    @app.errorhandler(413)
    def request_too_large(_error):
        return render_template(
            "index.html",
            error="Upload exceeds the configured per-request size limit.",
            history=list_analyses(app.config["DATABASE"]),
        ), 413

    @app.get("/")
    def index():
        return render_template(
            "index.html", history=list_analyses(app.config["DATABASE"])
        )

    @app.post("/analyze")
    def analyze():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return render_template(
                "index.html",
                error="Select a file to analyze.",
                history=list_analyses(app.config["DATABASE"]),
            ), 400

        try:
            with tempfile.TemporaryDirectory(prefix="bytescope-") as directory:
                file_path, safe_name = _save_upload(upload, directory)
                report = analyze_file(file_path, display_name=safe_name)
                analysis_id = save_analysis(app.config["DATABASE"], report)
        except ValueError as error:
            return render_template(
                "index.html",
                error=str(error),
                history=list_analyses(app.config["DATABASE"]),
            ), 400
        except OSError:
            logger.exception("Unable to analyze uploaded file")
            return render_template(
                "index.html",
                error="The file could not be read or the local history could not be saved.",
                history=list_analyses(app.config["DATABASE"]),
            ), 500

        return render_template(
            "index.html",
            report=report,
            report_id=analysis_id,
            history=list_analyses(app.config["DATABASE"]),
        )

    @app.post("/compare")
    def compare():
        left_upload = request.files.get("first_file")
        right_upload = request.files.get("second_file")
        if (
            left_upload is None
            or right_upload is None
            or not left_upload.filename
            or not right_upload.filename
        ):
            return render_template(
                "index.html",
                error="Choose both files to compare.",
                history=list_analyses(app.config["DATABASE"]),
            ), 400
        try:
            with tempfile.TemporaryDirectory(prefix="bytescope-compare-") as directory:
                left_path, left_name = _save_upload(left_upload, Path(directory) / "first")
                right_path, right_name = _save_upload(right_upload, Path(directory) / "second")
                comparison = compare_files(left_path, right_path)
                comparison["first_name"] = left_name
                comparison["second_name"] = right_name
        except ValueError as error:
            return render_template(
                "index.html",
                error=str(error),
                history=list_analyses(app.config["DATABASE"]),
            ), 400
        except OSError:
            logger.exception("Unable to compare uploaded files")
            return render_template(
                "index.html",
                error="The files could not be read for comparison.",
                history=list_analyses(app.config["DATABASE"]),
            ), 500
        return render_template(
            "index.html",
            comparison=comparison,
            history=list_analyses(app.config["DATABASE"]),
        )

    @app.get("/report/<analysis_id>.json")
    def export_report(analysis_id):
        report = get_analysis(app.config["DATABASE"], analysis_id)
        if report is None:
            return jsonify({"error": "Report not found"}), 404
        response = jsonify(report)
        response.headers["Content-Disposition"] = 'attachment; filename="bytescope-report.json"'
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
