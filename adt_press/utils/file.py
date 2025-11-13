import hashlib
import json
import os
import shutil
from functools import cache
from typing import Any

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


def write_json_file(file_path: str, data: Any, default=None) -> str:
    """
    Dumps JSON data to a file with UTF-8 encoding and specified indentation.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=default)

    return file_path


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


def copy_file(source_dir: str, dest_dir: str, relative_path: str) -> str:
    """
    Copy a file from source directory to destination directory.

    Args:
        source_dir: Source directory containing the original file
        dest_dir: Destination directory for copied files
        relative_path: Relative path of the file within source_dir

    Returns:
        Path relative to current working directory
    """
    original_path = os.path.join(source_dir, relative_path)
    filename = os.path.basename(relative_path)
    new_path = os.path.join(dest_dir, filename)

    if os.path.exists(original_path):
        shutil.copy2(original_path, new_path)

    # Return path relative to current working directory
    return os.path.relpath(new_path)
