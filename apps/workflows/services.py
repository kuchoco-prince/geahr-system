from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.permissions import user_role_codes
from apps.workflows.models import (
    WorkflowDefinition,
    WorkflowStep,
    ApprovalRequest,
    ApprovalAction,
)


# ---------------------------------------------------------------------
# Workflow lookup
# ---------------------------------------------------------------------

def _find_workflow(module: str, code: str, region_id=None) -> WorkflowDefinition:
    """
    Find an active workflow definition for (module, code).
    Preference:
      1) Region-specific workflow if region_id is provided
      2) Global workflow (region is null)
    """
    if region_id:
        wf = WorkflowDefinition.objects.filter(
            module=module,
            code=code,
            region_id=region_id,
            is_active=True,
        ).first()
        if wf:
            return wf

    wf = WorkflowDefinition.objects.filter(
        module=module,
        code=code,
        region__isnull=True,
        is_active=True,
    ).first()

    if not wf:
        raise ValidationError(f"No active workflow found for module={module} code={code}")

    return wf


# ---------------------------------------------------------------------
# Approval creation
# ---------------------------------------------------------------------

def create_approval(
    module: str,
    request_type: str,
    request_ref_id,
    created_by,
    region_id=None,
    assigned_to_user=None,  # optional: assign step 1 to a specific user
) -> ApprovalRequest:
    """
    Create an ApprovalRequest and set it to the first workflow step.
    """
    wf = _find_workflow(module, request_type, region_id=region_id)
    first_step = wf.steps.order_by("step_order").first()
    if not first_step:
        raise ValidationError("Workflow has no steps.")

    approval = ApprovalRequest.objects.create(
        module=module,
        request_type=request_type,
        request_ref_id=request_ref_id,
        region_id=region_id,
        created_by=created_by,
        status=ApprovalRequest.Status.PENDING,
        current_step_order=first_step.step_order,
        assigned_to_user=assigned_to_user,
    )
    return approval


# ---------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------

def is_user_approver_for_step(user, approval: ApprovalRequest, step: WorkflowStep) -> bool:
    """
    Authorization rules:
    1) If approval.assigned_to_user is set => ONLY that user can act (strict routing).
    2) Else:
       - If step rule is USER => step.approver_user must match user
       - If step rule is ROLE => step.approver_role_code must be in user's roles
    """
    if not user or not user.is_authenticated:
        return False

    # Strict assignment overrides everything
    if approval.assigned_to_user_id:
        return approval.assigned_to_user_id == user.id

    if step.approver_rule == WorkflowStep.Rule.USER:
        return step.approver_user_id == user.id

    if step.approver_rule == WorkflowStep.Rule.ROLE and step.approver_role_code:
        roles = set(user_role_codes(user))
        return step.approver_role_code in roles

    return False


# ---------------------------------------------------------------------
# Act on approval
# ---------------------------------------------------------------------

@transaction.atomic
def act_on_approval(*, approval: ApprovalRequest, user, action: str, comment: str = "") -> ApprovalRequest:
    """
    Perform APPROVE / REJECT / RETURN on an approval request.

    Behavior:
    - REJECT: ends workflow (status=REJECTED)
    - RETURN: ends workflow (status=RETURNED)
    - APPROVE: moves to next step; if none, marks APPROVED
      When moving to next step, assigned_to_user is cleared so role-based
      approvers can act on later steps (unless you re-assign elsewhere).
    """
    if approval.status != ApprovalRequest.Status.PENDING:
        raise ValidationError("This approval is not pending and cannot be acted on.")

    wf = _find_workflow(approval.module, approval.request_type, region_id=approval.region_id)
    step = wf.steps.filter(step_order=approval.current_step_order).first()
    if not step:
        raise ValidationError("Current workflow step not found.")

    if not is_user_approver_for_step(user, approval, step):
        raise ValidationError("You are not allowed to act on this approval step.")

    action = (action or "").upper().strip()
    if action not in {"APPROVE", "REJECT", "RETURN"}:
        raise ValidationError("Invalid action. Use APPROVE/REJECT/RETURN.")

    # Record action
    ApprovalAction.objects.create(
        request=approval,
        step_order=approval.current_step_order,
        actor=user,
        action=action,
        comment=comment or "",
    )

    # Terminal outcomes
    if action == "REJECT":
        approval.status = ApprovalRequest.Status.REJECTED
        approval.save(update_fields=["status", "updated_at"])
        return approval

    if action == "RETURN":
        approval.status = ApprovalRequest.Status.RETURNED
        approval.save(update_fields=["status", "updated_at"])
        return approval

    # APPROVE: move to next step or finish
    next_step = wf.steps.filter(step_order__gt=approval.current_step_order).order_by("step_order").first()

    if not next_step:
        approval.status = ApprovalRequest.Status.APPROVED
        approval.assigned_to_user = None
        approval.save(update_fields=["status", "assigned_to_user", "updated_at"])
        return approval

    # Move forward
    approval.current_step_order = next_step.step_order
    approval.assigned_to_user = None  # clear assignment; later steps can be role-based

    approval.save(update_fields=["current_step_order", "assigned_to_user", "updated_at"])
    return approval
