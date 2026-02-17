from django.db import models
from django.conf import settings

from apps.common.models import UUIDModel, TimeStampedModel
from apps.org.models import Region


class WorkflowDefinition(UUIDModel, TimeStampedModel):
    module = models.CharField(max_length=60, db_index=True)  # leave, exit, performance
    code = models.CharField(max_length=80, db_index=True)    # leave_senior, leave_supervisor, leave_junior_regional
    name = models.CharField(max_length=160)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("module", "code", "region")


class WorkflowStep(UUIDModel, TimeStampedModel):
    class Rule(models.TextChoices):
        ROLE = "ROLE", "Role"
        USER = "USER", "Specific User"

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="steps")
    step_order = models.PositiveIntegerField()

    approver_rule = models.CharField(max_length=20, choices=Rule.choices, default=Rule.ROLE)
    approver_role_code = models.CharField(max_length=60, blank=True)  # e.g., CEO, HR_HO, REGIONAL_MANAGER
    approver_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    required = models.BooleanField(default=True)

    class Meta:
        unique_together = ("workflow", "step_order")
        ordering = ["step_order"]


class ApprovalRequest(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        RETURNED = "RETURNED", "Returned"

    module = models.CharField(max_length=60, db_index=True)
    request_type = models.CharField(max_length=80, db_index=True)  # leave_senior etc.
    request_ref_id = models.UUIDField(db_index=True)

    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="approvals_created",
    )

    # ✅ if set, ONLY this user should see/act on the approval (employee-specific routing)
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approvals_assigned",
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    current_step_order = models.PositiveIntegerField(default=1)


class ApprovalAction(UUIDModel, TimeStampedModel):
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name="actions")
    step_order = models.PositiveIntegerField()

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20)  # APPROVE/REJECT/RETURN
    comment = models.TextField(blank=True)
