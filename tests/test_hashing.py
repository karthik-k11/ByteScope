from hashing import calculate_hashes
import hashlib


def test_hashing(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_bytes(b"ByteScope")

    result = calculate_hashes(test_file)

    expected_md5 = hashlib.md5(b"ByteScope").hexdigest()
    expected_sha256 = hashlib.sha256(b"ByteScope").hexdigest()

    assert result["md5"] == expected_md5
    assert result["sha256"] == expected_sha256