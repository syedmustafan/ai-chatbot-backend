"""
DocForge models: upload sessions, extracted records, and generated documents.

Generic by design so template packs (housing tribunal, NDAs, invoices, etc.)
can be added without schema changes.
"""
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class UploadSession(models.Model):
    """A single file upload, its extracted records, and its generated docs."""

    class PrivacyMode(models.TextChoices):
        EPHEMERAL = 'ephemeral', 'Ephemeral (wipe on download)'
        AUTO_EXPIRE = 'auto_expire', 'Auto-expire (24h)'
        RETAINED = 'retained', 'Retained (manual delete)'

    class Status(models.TextChoices):
        INCOMPLETE = 'incomplete', 'Incomplete'
        READY = 'ready', 'Ready'
        GENERATED = 'generated', 'Generated'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=255)
    source_path = models.CharField(max_length=512, blank=True)
    template_pack = models.CharField(max_length=64, default='housing_tribunal_pack')
    privacy_mode = models.CharField(
        max_length=16,
        choices=PrivacyMode.choices,
        default=PrivacyMode.AUTO_EXPIRE,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.INCOMPLETE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def set_expiry(self):
        """Seed expires_at based on privacy_mode."""
        if self.privacy_mode == self.PrivacyMode.EPHEMERAL:
            self.expires_at = timezone.now() + timedelta(hours=1)
        elif self.privacy_mode == self.PrivacyMode.AUTO_EXPIRE:
            self.expires_at = timezone.now() + timedelta(hours=24)
        else:
            self.expires_at = None

    def refresh_status(self):
        records = list(self.records.all())
        if self.documents_exist():
            self.status = self.Status.GENERATED
        elif records and all(not r.missing_fields for r in records):
            self.status = self.Status.READY
        else:
            self.status = self.Status.INCOMPLETE

    def documents_exist(self) -> bool:
        return GeneratedDocument.objects.filter(record__session=self).exists()


class ExtractedRecord(models.Model):
    """One row of parsed tabular data."""
    session = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name='records',
    )
    row_index = models.PositiveIntegerField()
    data = models.JSONField(default=dict)
    missing_fields = models.JSONField(default=list)

    class Meta:
        ordering = ['row_index']
        unique_together = ('session', 'row_index')


class GeneratedDocument(models.Model):
    """A rendered document tied to one record."""
    record = models.ForeignKey(
        ExtractedRecord,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    template_key = models.CharField(max_length=64)
    display_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['template_key']
