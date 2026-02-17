from apps.audit.models import AuditLog
from apps.audit.middleware import get_audit_context

def write_audit(action: str, entity_type: str, entity_id, before=None, after=None, note: str = ""):
    user, ip, ua = get_audit_context()
    AuditLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=user if getattr(user, "is_authenticated", False) else None,
        ip_address=ip or "",
        user_agent=ua or "",
        before_json=before,
        after_json=after,
        note=note or "",
    )
