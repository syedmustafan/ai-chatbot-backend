"""
Template pack registry.

Each pack declares required fields and a set of .docx templates. The DocForge
module is pack-agnostic — adding a new pack does not require schema changes.
"""
import json
from pathlib import Path
from typing import TypedDict

BASE = Path(__file__).resolve().parent


class TemplateEntry(TypedDict):
    key: str
    display_name: str
    filename: str


class PackConfig(TypedDict):
    key: str
    display_name: str
    required_fields: list[str]
    templates: list[TemplateEntry]


def load_pack(pack_key: str) -> PackConfig:
    pack_dir = BASE / pack_key
    with open(pack_dir / 'pack.json', 'r') as f:
        return json.load(f)


def pack_dir(pack_key: str) -> Path:
    return BASE / pack_key


def list_packs() -> list[dict]:
    out = []
    for child in BASE.iterdir():
        if child.is_dir() and (child / 'pack.json').exists():
            cfg = load_pack(child.name)
            out.append({'key': cfg['key'], 'display_name': cfg['display_name']})
    return out
