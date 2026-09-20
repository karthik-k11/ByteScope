from pathlib import Path


def analyze_file(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("File not found")

    return {
        "name": path.name,
        "extension": path.suffix,
        "size": path.stat().st_size
    }