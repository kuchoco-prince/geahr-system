from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel

class AuditLog(UUIDModel, TimeStampedModel):
    action = models.CharField(max_length=40, db_index=True)        # CREATE/UPDATE/SUBMIT/APPROVE etc.
    entity_type = models.CharField(max_length=80, db_index=True)   # LeaveRequest, Employee, ApprovalRequest...
    entity_id = models.UUIDField(db_index=True)

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.CharField(max_length=60, blank=True)
    user_agent = models.TextField(blank=True)

    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)

    note = models.TextField(blank=True)
