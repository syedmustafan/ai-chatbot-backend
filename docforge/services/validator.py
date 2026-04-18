"""
Per-record validation driven by the template pack's required_fields config.
"""
from ..template_packs import load_pack


def compute_missing_fields(record_data: dict, pack_key: str) -> list[str]:
    pack = load_pack(pack_key)
    required = pack.get('required_fields', [])
    missing = []
    for field in required:
        val = record_data.get(field)
        if val is None or str(val).strip() == '':
            missing.append(field)
    return missing
