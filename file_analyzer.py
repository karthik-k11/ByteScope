from pathlib import Path

from signatures import detect_file_type
from hashing import calculate_hashes
from hex_viewer import generate_hex_view


EXTENSION_MAP = {
    ".png": "PNG",
    ".pdf": "PDF",
    ".zip": "ZIP",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".wav": "WAV",
    ".mp3": "MP3",
    ".exe": "EXE",
}


def analyze_file(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("File not found")

    extension = path.suffix.lower()
    detected_type = detect_file_type(file_path)
    hashes = calculate_hashes(file_path)
    hex_preview = generate_hex_view(file_path)

    expected_type = EXTENSION_MAP.get(extension)

    return {
        "name": path.name,
        "extension": extension,
        "size": path.stat().st_size,
        "detected_type": detected_type,
        "extension_matches": (
            expected_type is None or expected_type == detected_type
        ),
        "md5": hashes["md5"],
        "sha256": hashes["sha256"],
        "hex_preview": hex_preview,
    }