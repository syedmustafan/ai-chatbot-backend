"""
Cleanup sweep for expired upload sessions.

Minimal logging — we only record session IDs and actions, never filenames
or extracted record contents (data minimization).
"""
import logging

from django.utils import timezone

from .. import storage
from ..models import UploadSession

log = logging.getLogger(__name__)


def wipe_session(session: UploadSession) -> None:
    """Immediately delete files + DB row for a session."""
    storage.delete_prefix(storage.session_key(session.id))
    sid = str(session.id)
    session.delete()
    log.info('docforge.wipe session=%s', sid)


def sweep() -> int:
    """Delete all sessions whose expires_at has passed. Returns count deleted."""
    now = timezone.now()
    expired = UploadSession.objects.exclude(expires_at=None).filter(expires_at__lt=now)
    count = 0
    for session in expired:
        wipe_session(session)
        count += 1
    log.info('docforge.sweep deleted=%s', count)
    return count
