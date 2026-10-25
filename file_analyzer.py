from pathlib import Path

from analysis_features import analyze_details
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
    ".webp": "WEBP",
    ".avi": "AVI",
    ".mp3": "MP3",
    ".exe": "EXE",
    ".gz": "GZIP",
    ".7z": "7-Zip",
    ".rar": "RAR",
    ".elf": "ELF",
    ".bmp": "BMP",
    ".ogg": "Ogg",
}


def analyze_file(file_path, display_name=None):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("File not found")

    name = display_name or path.name
    extension = Path(name).suffix.lower()
    detected_type = detect_file_type(file_path)
    hashes = calculate_hashes(file_path)
    hex_preview = generate_hex_view(file_path)
    details = analyze_details(file_path)

    expected_type = EXTENSION_MAP.get(extension)

    report = {
        "name": name,
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
    report.update(details)
    return report


def compare_files(first_path, second_path, chunk_size=65536, max_offsets=100):
    first = Path(first_path)
    second = Path(second_path)
    first_size = first.stat().st_size
    second_size = second.stat().st_size
    compared = 0
    different = 0
    first_offsets = []

    with first.open("rb") as left, second.open("rb") as right:
        while True:
            left_chunk = left.read(chunk_size)
            right_chunk = right.read(chunk_size)
            if not left_chunk and not right_chunk:
                break
            common = min(len(left_chunk), len(right_chunk))
            for index in range(common):
                if left_chunk[index] != right_chunk[index]:
                    different += 1
                    if len(first_offsets) < max_offsets:
                        first_offsets.append(compared + index)
            extra = abs(len(left_chunk) - len(right_chunk))
            if extra:
                different += extra
                if len(first_offsets) < max_offsets:
                    first_offsets.append(compared + common)
            compared += max(len(left_chunk), len(right_chunk))

    return {
        "first_name": first.name,
        "second_name": second.name,
        "first_size": first_size,
        "second_size": second_size,
        "equal": first_size == second_size and different == 0,
        "different_bytes": different,
        "first_differing_offsets": first_offsets,
        "offsets_truncated": different > len(first_offsets),
    }