"""
End-to-end tests for DocForge.

Uses FileSystemStorage pointed at a tempdir so the same code paths that hit
GCS in prod are exercised locally — no emulator required.
"""
import io
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from . import storage
from .models import ExtractedRecord, GeneratedDocument, UploadSession
from .services import cleanup

SAMPLE_XLSX = Path(__file__).resolve().parent / 'samples' / 'tenants.xlsx'

_tmpdir = tempfile.mkdtemp(prefix='docforge-test-')


@override_settings(MEDIA_ROOT=_tmpdir, USE_GCS=False)
class DocForgeFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _upload(self, privacy_mode='auto_expire'):
        with open(SAMPLE_XLSX, 'rb') as f:
            upload = SimpleUploadedFile(
                'tenants.xlsx',
                f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        return self.client.post(
            '/api/docforge/upload/',
            {'file': upload, 'privacy_mode': privacy_mode, 'template_pack': 'housing_tribunal_pack'},
            format='multipart',
        )

    def test_upload_xlsx_creates_records(self):
        r = self._upload()
        self.assertEqual(r.status_code, 201, r.content)
        session_id = r.data['id']
        session = UploadSession.objects.get(pk=session_id)
        records = list(session.records.order_by('row_index'))
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].missing_fields, [])
        self.assertIn('postal_code', records[1].missing_fields)
        self.assertIn('rent_amount', records[2].missing_fields)

    def test_patch_record_clears_missing_fields(self):
        r = self._upload()
        session_id = r.data['id']
        record = ExtractedRecord.objects.get(session_id=session_id, row_index=1)
        fixed = dict(record.data, postal_code='EC1A 1BB')
        patch = self.client.patch(
            f'/api/docforge/records/{record.id}/',
            {'data': fixed},
            format='json',
        )
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.data['missing_fields'], [])

    def _fill_and_generate(self, session_id):
        # Fill the two incomplete rows so generate succeeds.
        fixes = {1: {'postal_code': 'EC1A 1BB'}, 2: {'rent_amount': '1100'}}
        for idx, patch in fixes.items():
            rec = ExtractedRecord.objects.get(session_id=session_id, row_index=idx)
            self.client.patch(
                f'/api/docforge/records/{rec.id}/',
                {'data': dict(rec.data, **patch)},
                format='json',
            )
        return self.client.post(f'/api/docforge/sessions/{session_id}/generate/')

    def test_generate_then_zip_download(self):
        session_id = self._upload().data['id']
        gen = self._fill_and_generate(session_id)
        self.assertEqual(gen.status_code, 200, gen.content)
        docs = GeneratedDocument.objects.filter(record__session_id=session_id)
        self.assertEqual(docs.count(), 9)  # 3 rows * 3 templates

        zip_resp = self.client.get(f'/api/docforge/sessions/{session_id}/download/')
        self.assertEqual(zip_resp.status_code, 200)
        body = b''.join(zip_resp.streaming_content)
        zf = zipfile.ZipFile(io.BytesIO(body))
        names = zf.namelist()
        self.assertEqual(len(names), 9)
        self.assertTrue(all(n.endswith('.docx') for n in names))

    def test_ephemeral_wipe_on_download(self):
        session_id = self._upload(privacy_mode='ephemeral').data['id']
        self._fill_and_generate(session_id)
        resp = self.client.get(f'/api/docforge/sessions/{session_id}/download/')
        self.assertEqual(resp.status_code, 200)
        # Drain + trigger close() which fires the wipe callback.
        list(resp.streaming_content)
        resp.close()
        self.assertFalse(UploadSession.objects.filter(pk=session_id).exists())

    def test_sweep_deletes_expired(self):
        session_id = self._upload().data['id']
        UploadSession.objects.filter(pk=session_id).update(
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        deleted = cleanup.sweep()
        self.assertEqual(deleted, 1)
        self.assertFalse(UploadSession.objects.filter(pk=session_id).exists())

    def test_parse_rejects_unsupported_type(self):
        upload = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')
        r = self.client.post(
            '/api/docforge/upload/',
            {'file': upload},
            format='multipart',
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(UploadSession.objects.count(), 0)

    def test_sweep_endpoint_requires_token(self):
        from django.test import override_settings as _ov
        with _ov():
            import os
            os.environ['DOCFORGE_CLEANUP_TOKEN'] = 'secret-123'
            try:
                bad = self.client.post('/api/docforge/_internal/sweep/')
                self.assertEqual(bad.status_code, 403)
                good = self.client.post(
                    '/api/docforge/_internal/sweep/',
                    HTTP_X_CLEANUP_TOKEN='secret-123',
                )
                self.assertEqual(good.status_code, 200)
                self.assertIn('deleted', good.data)
            finally:
                os.environ.pop('DOCFORGE_CLEANUP_TOKEN', None)
