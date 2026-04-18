"""Storage helpers backed by Django's default_storage.

Works uniformly against FileSystemStorage (dev/tests) and GoogleCloudStorage
(prod) so the rest of the app never touches filesystem paths directly.
"""
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def session_key(session_id, *parts: str) -> str:
    return "/".join(["docforge", str(session_id), *parts])


def save_bytes(key: str, data: bytes) -> str:
    return default_storage.save(key, ContentFile(data))


def open_read(key: str):
    return default_storage.open(key, "rb")


def exists(key: str) -> bool:
    return default_storage.exists(key)


def delete(key: str) -> None:
    if default_storage.exists(key):
        default_storage.delete(key)


def delete_prefix(prefix: str) -> None:
    try:
        dirs, files = default_storage.listdir(prefix)
    except (FileNotFoundError, OSError):
        return
    for f in files:
        default_storage.delete(f"{prefix}/{f}")
    for d in dirs:
        delete_prefix(f"{prefix}/{d}")
