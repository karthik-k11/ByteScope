from signatures import detect_file_type


def test_png_detection(tmp_path):
    test_file = tmp_path / "sample.png"

    png_signature = bytes.fromhex(
        "89 50 4E 47 0D 0A 1A 0A"
    )

    test_file.write_bytes(png_signature)

    assert detect_file_type(test_file) == "PNG"


def test_unknown_file(tmp_path):
    test_file = tmp_path / "unknown.bin"

    test_file.write_bytes(b"ByteScope")

    assert detect_file_type(test_file) == "Unknown"


def test_empty_zip_and_riff_subtypes_are_identified(tmp_path):
    test_file = tmp_path / "empty.zip"
    test_file.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    assert detect_file_type(test_file) == "ZIP"

    webp_file = tmp_path / "image.bin"
    webp_file.write_bytes(b"RIFF" + b"\x00" * 4 + b"WEBP")
    assert detect_file_type(webp_file) == "WEBP"