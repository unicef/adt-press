import hashlib

from fsspec import open


def calculate_file_hash(file_path: str) -> str:
    """Calculate the hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()
