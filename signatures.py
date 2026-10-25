SIGNATURES = {
    "PNG": bytes.fromhex("89 50 4E 47 0D 0A 1A 0A"),
    "PDF": b"%PDF",
    "ZIP": b"PK\x03\x04",
    "JPEG": bytes.fromhex("FF D8 FF"),
    "GIF": b"GIF8",
    "WAV": b"RIFF",
    "MP3": b"ID3",
    "EXE": b"MZ",
    "GZIP": bytes.fromhex("1F 8B"),
    "7-Zip": b"7z\xbc\xaf\x27\x1c",
    "RAR": b"Rar!\x1a\x07",
    "ELF": b"\x7fELF",
    "BMP": b"BM",
    "Ogg": b"OggS",
}


def identify_header(header):
    if header.startswith(b"PK") and header[2:4] in (b"\x03\x04", b"\x05\x06", b"\x07\x08"):
        return "ZIP"
    if header.startswith(b"RIFF") and len(header) >= 12:
        if header[8:12] == b"WAVE":
            return "WAV"
        if header[8:12] == b"WEBP":
            return "WEBP"
        if header[8:12] == b"AVI ":
            return "AVI"

    for file_type, signature in SIGNATURES.items():
        if header.startswith(signature):
            return file_type

    return "Unknown"


def detect_file_type(file_path):
    with open(file_path, "rb") as file:
        return identify_header(file.read(16))
