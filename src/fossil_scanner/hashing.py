"""SHA-256 hashing utilities. Used to bind provenance to file bytes."""
import hashlib
from typing import Iterator

_CHUNK = 65536


def hash_file(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            sha.update(chunk)
    return sha.hexdigest()


def hash_data(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_stream(chunks: Iterator[bytes]) -> str:
    sha = hashlib.sha256()
    for chunk in chunks:
        sha.update(chunk)
    return sha.hexdigest()
