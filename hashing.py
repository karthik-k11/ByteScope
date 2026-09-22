import hashlib


def calculate_hashes(file_path, chunk_size=8192):
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    return {
        "md5": md5_hash.hexdigest(),
        "sha256": sha256_hash.hexdigest()
    }