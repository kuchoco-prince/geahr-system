from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel


class Document(UUIDModel, TimeStampedModel):
    class OwnerType(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        LEAVE = "LEAVE", "Leave"
        HR_REQUEST = "HR_REQUEST", "HR Request"
        LETTER = "LETTER", "Letter"
        ASSET = "ASSET", "Asset"
        EXIT = "EXIT", "Exit"
        PERFORMANCE = "PERFORMANCE", "Performance"
        OTHER = "OTHER", "Other"

    owner_type = models.CharField(max_length=30, choices=OwnerType.choices, db_index=True)
    owner_id = models.UUIDField(db_index=True)

    doc_type = models.CharField(max_length=80, db_index=True)  # e.g. LEAVE_APPROVAL_LETTER
    title = models.CharField(max_length=200, blank=True)

    file = models.FileField(upload_to="documents/%Y/%m/")
    version = models.PositiveIntegerField(default=1)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    access_scope = models.CharField(max_length=60, default="HR_ONLY")  # HR_ONLY / MANAGEMENT / OWNER / PUBLIC

    class Meta:
        indexes = [
            models.Index(fields=["owner_type", "owner_id"]),
            models.Index(fields=["doc_type"]),
        ]
