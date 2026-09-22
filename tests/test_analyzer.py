from file_analyzer import analyze_file


def test_analyze_file(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("ByteScope")

    result = analyze_file(test_file)

    assert result["name"] == "sample.txt"
    assert result["extension"] == ".txt"
    assert result["size"] == 9
    assert result["detected_type"] == "Unknown"
    assert result["extension_matches"] is True


def test_missing_file():
    missing_file = "does_not_exist.bin"

    try:
        analyze_file(missing_file)
        assert False
    except FileNotFoundError:
        assert True