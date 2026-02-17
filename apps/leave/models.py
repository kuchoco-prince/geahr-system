from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel
from apps.employees.models import Employee
from apps.documents.models import Document
from apps.workflows.models import ApprovalRequest


class LeaveRequest(UUIDModel, TimeStampedModel):
    class LeaveType(models.TextChoices):
        ANNUAL = "ANNUAL", "Annual Leave"
        SICK = "SICK", "Sick Leave"
        STUDY = "STUDY", "Study Leave"
        MATERNITY = "MATERNITY", "Maternity Leave"
        PATERNITY = "PATERNITY", "Paternity Leave"
        COMPASSIONATE = "COMPASSIONATE", "Compassionate Leave"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        RETURNED = "RETURNED", "Returned"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices, default=LeaveType.ANNUAL)

    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.PositiveIntegerField(default=0)

    reason = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Approval workflow request that tracks steps/approvals
    approval_request = models.ForeignKey(ApprovalRequest, null=True, blank=True, on_delete=models.SET_NULL)

    # HR-issued approval letter / notification (required by GEA process)
    approval_letter = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL)

    # Store last action note (approve/reject comment) for traceability
    last_action_note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["leave_type", "status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
