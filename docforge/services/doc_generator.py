"""
Render .docx templates with per-record context; bundle outputs into a ZIP.
"""
import io
import os
import tempfile
import zipfile
from pathlib import Path

from django.core.files.storage import default_storage
from docxtpl import DocxTemplate

from .. import storage
from ..models import GeneratedDocument, UploadSession
from ..template_packs import load_pack, pack_dir


def generate_for_session(session: UploadSession) -> list[GeneratedDocument]:
    pack = load_pack(session.template_pack)
    pack_path = pack_dir(session.template_pack)
    created: list[GeneratedDocument] = []

    # Clear any previous outputs for this session (user can regenerate).
    for old in GeneratedDocument.objects.filter(record__session=session):
        storage.delete(old.file_path)
        old.delete()

    for record in session.records.all():
        for tpl in pack['templates']:
            template_path = pack_path / tpl['filename']
            doc = DocxTemplate(str(template_path))
            doc.render(record.data)
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                doc.save(tmp_path)
                with open(tmp_path, 'rb') as f:
                    rendered = f.read()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            filename = f"row{record.row_index}_{tpl['key']}.docx"
            key = storage.session_key(session.id, 'generated', filename)
            saved_key = storage.save_bytes(key, rendered)
            created.append(
                GeneratedDocument.objects.create(
                    record=record,
                    template_key=tpl['key'],
                    display_name=tpl['display_name'],
                    file_path=saved_key,
                )
            )
    return created


def build_zip_for_session(session: UploadSession) -> str:
    docs = GeneratedDocument.objects.filter(record__session=session).select_related('record')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d in docs:
            if not storage.exists(d.file_path):
                continue
            with storage.open_read(d.file_path) as src:
                zf.writestr(Path(d.file_path).name, src.read())
    zip_key = storage.session_key(session.id, f'docforge_{session.id}.zip')
    # Overwrite any existing zip so successive downloads reflect latest docs.
    storage.delete(zip_key)
    return storage.save_bytes(zip_key, buf.getvalue())
