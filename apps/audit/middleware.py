import threading

_state = threading.local()

def set_audit_context(user=None, ip="", ua=""):
    _state.user = user
    _state.ip = ip
    _state.ua = ua

def get_audit_context():
    return (
        getattr(_state, "user", None),
        getattr(_state, "ip", ""),
        getattr(_state, "ua", ""),
    )

class AuditContextMiddleware:
    """
    Stores request context so audit logs can capture actor + IP + user-agent.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
        ua = request.META.get("HTTP_USER_AGENT", "")
        set_audit_context(getattr(request, "user", None), ip, ua)
        return self.get_response(request)
