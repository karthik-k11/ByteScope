import math
import struct
import zlib
import zipfile

from analysis_features import analyze_details
from file_analyzer import analyze_file, compare_files


def _png_chunk(kind, data):
    crc = zlib.crc32(kind + data)
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def test_entropy_and_printable_strings_are_reported(tmp_path):
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"ABCD" * 64)

    details = analyze_details(sample)

    assert details["entropy"] == round(math.log2(4), 4)
    assert any(value.startswith("ABCD") for value in details["strings"])


def test_embedded_signature_crossing_read_boundary_is_found(tmp_path):
    sample = tmp_path / "embedded.bin"
    prefix = b"x" * (65536 - 3)
    sample.write_bytes(prefix + b"\x89PNG\r\n\x1a\n" + b"tail")

    details = analyze_details(sample)

    assert any(
        item["type"] == "PNG" and item["offset"] == len(prefix)
        for item in details["embedded_signatures"]
    )
    assert details["carving_candidates"][0]["estimated_size"] == 12


def test_long_result_lists_are_capped_and_marked(tmp_path):
    sample = tmp_path / "busy.bin"
    sample.write_bytes(
        b"\x00".join([b"text"] * 301)
        + b"\x00"
        + b"\x00".join([b"\x89PNG\r\n\x1a\n"] * 251)
    )

    details = analyze_details(sample)

    assert len(details["strings"]) == 300
    assert details["strings_truncated"] is True
    assert len(details["embedded_signatures"]) == 250
    assert details["embedded_signatures_truncated"] is True


def test_png_chunk_checksum_and_missing_end_are_reported(tmp_path):
    sample = tmp_path / "sample.png"
    broken_idat = _png_chunk(b"IDAT", b"pixels")
    broken_idat = broken_idat[:-1] + bytes([broken_idat[-1] ^ 1])
    sample.write_bytes(b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", b"data") + broken_idat)

    report = analyze_file(sample)

    assert report["structures"]["PNG"]["chunks"][0]["crc_valid"] is True
    assert any("Checksum mismatch" in issue for issue in report["corruption_indicators"])
    assert any("IEND" in issue for issue in report["corruption_indicators"])


def test_pdf_page_marker_is_not_counted_twice_across_chunks(tmp_path):
    sample = tmp_path / "sample.pdf"
    marker = b"/Type /Page\n"
    sample.write_bytes(
        b"%PDF-1.5\n"
        + b"x" * (131057 - len(b"%PDF-1.5\n"))
        + marker
        + b"q" * 65536
        + b"%%EOF"
    )

    report = analyze_file(sample)

    assert report["structures"]["PDF"]["pages"] == 1


def test_zip_structure_lists_metadata_without_extracting(tmp_path):
    sample = tmp_path / "archive.zip"
    with zipfile.ZipFile(sample, "w") as archive:
        archive.writestr("folder/readme.txt", "not extracted")

    report = analyze_file(sample)

    assert report["structures"]["ZIP"]["entries"][0]["name"] == "folder/readme.txt"
    assert report["structures"]["ZIP"]["entries"][0]["size"] == len("not extracted")
    assert not (tmp_path / "folder").exists()


def test_binary_comparison_reports_differences_and_size_tail(tmp_path):
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"abc")
    second.write_bytes(b"axcd")

    result = compare_files(first, second)

    assert result["equal"] is False
    assert result["different_bytes"] == 2
    assert result["first_differing_offsets"] == [1, 3]


def test_identical_files_compare_equal(tmp_path):
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"identical")
    second.write_bytes(b"identical")

    assert compare_files(first, second)["equal"] is True
