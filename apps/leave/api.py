from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.core.exceptions import ValidationError

from apps.accounts.permissions import (
    IsAdminOrReadOnlyHRCEOOrSupervisor,
    RegionScopedQueryMixin,
)
from apps.employees.models import Employment
from apps.leave.models import LeaveRequest
from apps.workflows.services import create_approval
from apps.audit.services import write_audit


# ---------------------------------------------------------------------
# Workflow selection logic
# ---------------------------------------------------------------------

def pick_leave_workflow_code(employee) -> str:
    active = (
        Employment.objects
        .filter(employee=employee, status="ACTIVE")
        .order_by("-created_at")
        .first()
    )
    if not active:
        raise ValidationError("Employee has no ACTIVE employment record.")

    cat = active.staff_category

    if cat == "JUNIOR":
        return "leave_junior_regional"

    if cat == "SUPERVISOR":
        return "leave_supervisor"

    return "leave_senior"  # default


# ---------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = "__all__"


# ---------------------------------------------------------------------
# ViewSet
# ---------------------------------------------------------------------

class LeaveRequestViewSet(RegionScopedQueryMixin, viewsets.ModelViewSet):
    """
    Leave lifecycle:

    - DRAFT
    - SUBMITTED (creates ApprovalRequest)
    - APPROVED / REJECTED / RETURNED (synced by approvals endpoint)

    Access:
    - SYSTEM_ADMIN: full
    - HR/CEO: read-only
    - Supervisors: scoped access
    """

    queryset = (
        LeaveRequest.objects
        .select_related("employee", "approval_request")
        .all()
        .order_by("-created_at")
    )

    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminOrReadOnlyHRCEOOrSupervisor]

    # Used by RegionScopedQueryMixin
    region_field = "employee__employments__region"

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset(), self.request).distinct()

    # -----------------------------------------------------------------
    # SUBMIT ACTION
    # -----------------------------------------------------------------

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        lr = self.get_object()

        if lr.status != "DRAFT":
            return Response(
                {"error": "Only DRAFT leave can be submitted"},
                status=400,
            )

        active = (
            Employment.objects
            .filter(employee=lr.employee, status="ACTIVE")
            .order_by("-created_at")
            .first()
        )

        if not active:
            return Response(
                {"error": "Employee has no active employment record"},
                status=400,
            )

        # Determine workflow
        workflow_code = pick_leave_workflow_code(lr.employee)

        # Create approval
        approval = create_approval(
            module="leave",
            request_type=workflow_code,
            request_ref_id=lr.id,
            created_by=request.user,
            region_id=active.region_id,
        )

        # --------------------------------------------------------------
        # UNIQUE SUPERVISOR ROUTING (GEA requirement)
        # --------------------------------------------------------------
        # Senior leave should go to that employee's exact supervisor

        if workflow_code == "leave_senior":
            if not active.supervisor or not active.supervisor.user:
                return Response(
                    {"error": "Supervisor user not set for this employee"},
                    status=400,
                )

            approval.assigned_to_user = active.supervisor.user
            approval.save(update_fields=["assigned_to_user", "updated_at"])

        # Update leave status
        before = {
            "status": lr.status,
            "approval_request": str(lr.approval_request_id)
            if lr.approval_request_id
            else None,
        }

        lr.approval_request = approval
        lr.status = "SUBMITTED"
        lr.save(update_fields=["approval_request", "status", "updated_at"])

        write_audit(
            action="SUBMIT_LEAVE",
            entity_type="LeaveRequest",
            entity_id=lr.id,
            before=before,
            after={"status": lr.status, "workflow": workflow_code},
        )

        return Response(
            {
                "ok": True,
                "leave_request_id": str(lr.id),
                "approval_request_id": str(approval.id),
                "workflow_used": workflow_code,
            }
        )
