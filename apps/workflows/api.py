from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status

from apps.accounts.permissions import IsAdminOrReadOnlyHRCEOOrSupervisor, user_role_codes
from apps.workflows.models import ApprovalRequest, WorkflowStep
from apps.workflows.services import act_on_approval, _find_workflow
from apps.leave.models import LeaveRequest
from apps.audit.services import write_audit


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = "__all__"


class ApprovalActionInputSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT", "RETURN"])
    comment = serializers.CharField(required=False, allow_blank=True)


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Approvals Inbox + Acting endpoint.
    Access: any authenticated user.
    Enforcement of who can act is done inside workflows.services.act_on_approval()
    """
    queryset = ApprovalRequest.objects.all().order_by("-created_at")
    serializer_class = ApprovalRequestSerializer
    from apps.accounts.permissions import IsAdminOrReadOnlyHRCEOOrSupervisor

class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApprovalRequest.objects.all().order_by("-created_at")
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAdminOrReadOnlyHRCEOOrSupervisor]


    @action(detail=False, methods=["get"])
    def inbox(self, request):
        """
        Returns approvals the user should act on.

        Priority:
        1) Approvals assigned directly to this user (assigned_to_user)
        2) Approvals where current step matches user's role/user rules
        """
        # 1) Direct assignment (unique supervisor routing, etc.)
        assigned_qs = ApprovalRequest.objects.filter(
            status=ApprovalRequest.Status.PENDING,
            assigned_to_user=request.user,
        ).order_by("-created_at")

        if assigned_qs.exists():
            return Response(ApprovalRequestSerializer(assigned_qs, many=True).data)

        # 2) Role/user step-based matching
        roles = set(user_role_codes(request.user))
        matched_ids = []

        for ar in ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING).only(
            "id", "module", "request_type", "region_id", "current_step_order"
        ):
            try:
                wf = _find_workflow(ar.module, ar.request_type, region_id=ar.region_id)
            except Exception:
                # If workflow not found, skip it (shouldn't happen if seeded correctly)
                continue

            step = wf.steps.filter(step_order=ar.current_step_order).first()
            if not step:
                continue

            if step.approver_rule == WorkflowStep.Rule.USER and step.approver_user_id == request.user.id:
                matched_ids.append(ar.id)
            elif step.approver_rule == WorkflowStep.Rule.ROLE and step.approver_role_code and step.approver_role_code in roles:
                matched_ids.append(ar.id)

        qs = ApprovalRequest.objects.filter(id__in=matched_ids).order_by("-created_at")
        return Response(ApprovalRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def act(self, request, pk=None):
        """
        Approve/Reject/Return an approval request.
        """
        ar = self.get_object()

        payload = ApprovalActionInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        before = {"status": ar.status, "step": ar.current_step_order}

        try:
            updated = act_on_approval(
                approval=ar,
                user=request.user,
                action=payload.validated_data["action"],
                comment=payload.validated_data.get("comment", ""),
            )
        except DjangoValidationError as e:
            # Convert Django ValidationError to a proper DRF response
            msg = e.message if hasattr(e, "message") else str(e)
            return Response({"error": msg}, status=drf_status.HTTP_400_BAD_REQUEST)

        # Audit approval action
        write_audit(
            action="APPROVAL_ACTION",
            entity_type="ApprovalRequest",
            entity_id=updated.id,
            before=before,
            after={"status": updated.status, "step": updated.current_step_order},
            note=payload.validated_data.get("comment", ""),
        )

        # ---- LEAVE STATUS SYNC (GEA workflows) ----
        if updated.module == "leave" and updated.request_type in [
            "leave_senior",
            "leave_supervisor",
            "leave_junior_regional",
        ]:
            lr = LeaveRequest.objects.get(id=updated.request_ref_id)

            lr.last_action_note = payload.validated_data.get("comment", "")

            if updated.status == ApprovalRequest.Status.APPROVED:
                lr.status = "APPROVED"
            elif updated.status == ApprovalRequest.Status.REJECTED:
                lr.status = "REJECTED"
            elif updated.status == ApprovalRequest.Status.RETURNED:
                lr.status = "RETURNED"
            else:
                lr.status = "SUBMITTED"

            lr.save(update_fields=["status", "last_action_note", "updated_at"])

            write_audit(
                action="SYNC_STATUS",
                entity_type="LeaveRequest",
                entity_id=lr.id,
                before=None,
                after={"status": lr.status},
            )

        return Response(ApprovalRequestSerializer(updated).data)
