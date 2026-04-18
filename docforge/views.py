"""
DocForge API views — no auth for the demo.
"""
import hmac
import io
import os
import tempfile
import zipfile
from pathlib import Path

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import storage
from .models import ExtractedRecord, GeneratedDocument, UploadSession
from .serializers import (
    ExtractedRecordSerializer,
    UploadSessionListSerializer,
    UploadSessionSerializer,
)
from .services import cleanup, doc_generator
from .services.excel_parser import parse_xlsx
from .services.pdf_parser import parse_pdf
from .services.validator import compute_missing_fields
from .template_packs import list_packs


def _save_upload(session: UploadSession, django_file) -> str:
    buf = io.BytesIO()
    for chunk in django_file.chunks():
        buf.write(chunk)
    key = storage.session_key(session.id, "source", django_file.name)
    return storage.save_bytes(key, buf.getvalue())


def _download_to_temp(key: str, suffix: str) -> str:
    """Copy a storage object to a local temp file; return its path.

    Parsers need a real filesystem path. Caller is responsible for deleting.
    """
    with storage.open_read(key) as src:
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)
    return tmp_path


class PacksView(APIView):
    def get(self, request):
        return Response(list_packs())


class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

        privacy_mode = request.data.get('privacy_mode', UploadSession.PrivacyMode.AUTO_EXPIRE)
        template_pack = request.data.get('template_pack', 'housing_tribunal_pack')

        if privacy_mode not in UploadSession.PrivacyMode.values:
            return Response({'error': 'invalid privacy_mode'}, status=status.HTTP_400_BAD_REQUEST)

        ext = Path(f.name).suffix.lower()
        if ext not in ('.xlsx', '.pdf'):
            return Response(
                {'error': 'Only .xlsx and .pdf are supported'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = UploadSession(
            original_filename=f.name,
            privacy_mode=privacy_mode,
            template_pack=template_pack,
        )
        session.set_expiry()
        session.save()

        saved_key = _save_upload(session, f)
        session.source_path = saved_key
        session.save(update_fields=['source_path'])

        tmp_path = None
        try:
            tmp_path = _download_to_temp(saved_key, ext)
            if ext == '.xlsx':
                rows = parse_xlsx(tmp_path)
            else:
                rows = parse_pdf(tmp_path)
        except Exception as e:
            cleanup.wipe_session(session)
            return Response({'error': f'parse failed: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        for idx, row in enumerate(rows):
            ExtractedRecord.objects.create(
                session=session,
                row_index=idx,
                data=row,
                missing_fields=compute_missing_fields(row, template_pack),
            )

        session.refresh_status()
        session.save(update_fields=['status'])

        return Response(
            UploadSessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class SessionListView(APIView):
    def get(self, request):
        qs = UploadSession.objects.all()[:50]
        return Response(UploadSessionListSerializer(qs, many=True).data)


class SessionDetailView(APIView):
    parser_classes = [JSONParser]

    def get(self, request, session_id):
        try:
            session = UploadSession.objects.get(pk=session_id)
        except UploadSession.DoesNotExist:
            raise Http404
        return Response(UploadSessionSerializer(session).data)

    def delete(self, request, session_id):
        try:
            session = UploadSession.objects.get(pk=session_id)
        except UploadSession.DoesNotExist:
            raise Http404
        cleanup.wipe_session(session)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecordDetailView(APIView):
    parser_classes = [JSONParser]

    def patch(self, request, record_id):
        try:
            record = ExtractedRecord.objects.select_related('session').get(pk=record_id)
        except ExtractedRecord.DoesNotExist:
            raise Http404
        data = request.data.get('data')
        if not isinstance(data, dict):
            return Response({'error': 'data must be an object'}, status=status.HTTP_400_BAD_REQUEST)
        record.data = data
        record.missing_fields = compute_missing_fields(data, record.session.template_pack)
        record.save(update_fields=['data', 'missing_fields'])
        record.session.refresh_status()
        record.session.save(update_fields=['status'])
        return Response(ExtractedRecordSerializer(record).data)


class GenerateView(APIView):
    def post(self, request, session_id):
        try:
            session = UploadSession.objects.get(pk=session_id)
        except UploadSession.DoesNotExist:
            raise Http404
        records = list(session.records.all())
        if not records:
            return Response({'error': 'no records to generate'}, status=status.HTTP_400_BAD_REQUEST)
        blocked = [r.row_index for r in records if r.missing_fields]
        if blocked:
            return Response(
                {'error': 'some rows still have missing fields', 'row_indexes': blocked},
                status=status.HTTP_400_BAD_REQUEST,
            )
        doc_generator.generate_for_session(session)
        session.refresh_status()
        session.save(update_fields=['status'])
        return Response(UploadSessionSerializer(session).data)


class DocumentDownloadView(APIView):
    def get(self, request, document_id):
        try:
            doc = GeneratedDocument.objects.get(pk=document_id)
        except GeneratedDocument.DoesNotExist:
            raise Http404
        if not storage.exists(doc.file_path):
            raise Http404
        filename = Path(doc.file_path).name
        return FileResponse(
            storage.open_read(doc.file_path),
            as_attachment=True,
            filename=filename,
        )


class SessionZipDownloadView(APIView):
    def get(self, request, session_id):
        try:
            session = UploadSession.objects.get(pk=session_id)
        except UploadSession.DoesNotExist:
            raise Http404
        if not session.documents_exist():
            return Response({'error': 'no documents generated yet'}, status=status.HTTP_400_BAD_REQUEST)

        zip_key = doc_generator.build_zip_for_session(session)
        session.downloaded_at = timezone.now()
        session.save(update_fields=['downloaded_at'])

        response = FileResponse(
            storage.open_read(zip_key),
            as_attachment=True,
            filename=f'docforge_{session.id}.zip',
        )

        # Ephemeral mode: wipe after the response streams out.
        if session.privacy_mode == UploadSession.PrivacyMode.EPHEMERAL:
            sid = str(session.id)
            session.delete()
            _schedule_prefix_wipe(response, storage.session_key(sid))

        return response


def _schedule_prefix_wipe(response, prefix: str):
    original_close = response.close

    def _close_and_wipe():
        try:
            original_close()
        finally:
            storage.delete_prefix(prefix)

    response.close = _close_and_wipe


class SweepView(APIView):
    """Cron-triggered endpoint. Protected by a shared token in X-Cleanup-Token."""

    def post(self, request):
        expected = (os.environ.get('DOCFORGE_CLEANUP_TOKEN') or '').strip()
        provided = (request.headers.get('X-Cleanup-Token') or '').strip()
        if not expected or not hmac.compare_digest(expected, provided):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'deleted': cleanup.sweep()})
