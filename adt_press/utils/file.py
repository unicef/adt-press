import hashlib
from functools import cache

from fsspec import open


def write_file(output_path: str, bs: bytes, suffix: str = "") -> str:
    """Writes bytes to the specified output path, optionally appending a suffix to the filename."""

    # if we have a suffix, add it in after removing the extension
    if suffix != "":
        output_path = output_path.rsplit(".", 1)[0] + f"_{suffix}." + output_path.rsplit(".", 1)[1]

    with open(output_path, "wb") as f:
        f.write(bs)

    return output_path


def write_text_file(output_path: str, content: str) -> str:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def read_file(file_path: str) -> bytes:
    """Read the content of a file."""
    with open(file_path, "rb") as file:
        return bytes(file.read())


@cache
def cached_read_file(file_path: str) -> bytes:
    """Read the content of a file, caching the result."""
    return read_file(file_path)


def read_text_file(file_path: str) -> str:
    """Read the content of a text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return str(file.read())


@cache
def cached_read_text_file(file_path: str) -> str:
    return read_text_file(file_path)


def calculate_file_hash(file_path: str) -> str:
    """Calculate the hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()
