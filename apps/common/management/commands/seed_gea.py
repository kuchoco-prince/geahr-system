from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.accounts.models import Role, UserRole
from apps.workflows.models import WorkflowDefinition, WorkflowStep
from apps.org.models import Region, Department, Position, Grade


class Command(BaseCommand):
    help = "Seed GEA baseline data (roles, workflows, admin user)"

    def handle(self, *args, **options):
        User = get_user_model()

        # --- Roles required for GEA leave ---
        role_codes = [
            ("REGIONAL_MANAGER", "Regional Manager"),
            ("SUPERVISOR", "Supervisor / Unit Head"),
            ("CEO", "Chief Executive Officer"),
            ("HR_HO", "HR Directorate (Head Office)"),
            ("HR_REGIONAL", "HR Regional"),
            ("DIRECTOR_ADMIN", "Director Administration"),
            ("IT_ADMIN", "IT Admin"),
            ("AUDITOR", "Auditor"),
        ]
        roles = {}
        for code, name in role_codes:
            r, _ = Role.objects.get_or_create(code=code, defaults={"name": name})
            roles[code] = r

        # --- Create admin user ---
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@gea.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("Admin@12345")
            admin_user.save()

        # Give admin key roles
        for code in ["IT_ADMIN", "HR_HO", "CEO"]:
            UserRole.objects.get_or_create(user=admin_user, role=roles[code])

        # --- Org base ---
        ra, _ = Region.objects.get_or_create(name="Greater Accra")
        dept, _ = Department.objects.get_or_create(name="HR Directorate", parent=None)
        pos, _ = Position.objects.get_or_create(title="Staff")
        grade, _ = Grade.objects.get_or_create(name="G1", defaults={"rank_order": 1})

        # --- Workflows (GEA leave) ---
        # 1) Junior Officer (Regional) -> Regional Manager only
        wf1, _ = WorkflowDefinition.objects.get_or_create(
            module="leave", code="leave_junior_regional",
            defaults={"name": "Leave - Junior Officer (Regional)", "is_active": True, "region": None}
        )
        wf1.steps.all().delete()
        WorkflowStep.objects.create(workflow=wf1, step_order=1, approver_rule="ROLE", approver_role_code="REGIONAL_MANAGER", required=True)

        # 2) Senior Officer -> Supervisor -> CEO -> HR Directorate
        wf2, _ = WorkflowDefinition.objects.get_or_create(
            module="leave", code="leave_senior",
            defaults={"name": "Leave - Senior Officer", "is_active": True, "region": None}
        )
        wf2.steps.all().delete()
        WorkflowStep.objects.create(workflow=wf2, step_order=1, approver_rule="ROLE", approver_role_code="SUPERVISOR", required=True)
        WorkflowStep.objects.create(workflow=wf2, step_order=2, approver_rule="ROLE", approver_role_code="CEO", required=True)
        WorkflowStep.objects.create(workflow=wf2, step_order=3, approver_rule="ROLE", approver_role_code="HR_HO", required=True)

        # 3) Supervisor -> CEO -> HR Directorate
        wf3, _ = WorkflowDefinition.objects.get_or_create(
            module="leave", code="leave_supervisor",
            defaults={"name": "Leave - Supervisor", "is_active": True, "region": None}
        )
        wf3.steps.all().delete()
        WorkflowStep.objects.create(workflow=wf3, step_order=1, approver_rule="ROLE", approver_role_code="CEO", required=True)
        WorkflowStep.objects.create(workflow=wf3, step_order=2, approver_rule="ROLE", approver_role_code="HR_HO", required=True)

        self.stdout.write(self.style.SUCCESS("✅ Seed complete. Admin: admin / Admin@12345"))
