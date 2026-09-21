SIGNATURES = {
    "PNG": bytes.fromhex("89 50 4E 47 0D 0A 1A 0A"),
    "PDF": bytes.fromhex("25 50 44 46"),
    "ZIP": bytes.fromhex("50 4B 03 04"),
    "JPEG": bytes.fromhex("FF D8 FF"),
    "GIF": bytes.fromhex("47 49 46 38"),
    "WAV": bytes.fromhex("52 49 46 46"),
    "MP3": bytes.fromhex("49 44 33"),
    "EXE": bytes.fromhex("4D 5A"),
}


def detect_file_type(file_path):
    with open(file_path, "rb") as file:
        header = file.read(16)

    for file_type, signature in SIGNATURES.items():
        if header.startswith(signature):
            return file_type

    return "Unknown"