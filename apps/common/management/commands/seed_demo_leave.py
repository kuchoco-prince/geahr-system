from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.accounts.models import Role, UserRole
from apps.org.models import Region, Department, Position, Grade
from apps.employees.models import Employee, Employment


class Command(BaseCommand):
    help = "Create demo users/employees for testing GEA leave workflows"

    def handle(self, *args, **options):
        User = get_user_model()

        # Ensure base org data
        region, _ = Region.objects.get_or_create(name="Greater Accra")
        dept, _ = Department.objects.get_or_create(name="IT", parent=None)
        pos, _ = Position.objects.get_or_create(title="Officer")
        grade, _ = Grade.objects.get_or_create(name="G1", defaults={"rank_order": 1})

        # Roles
        def role(code, name):
            return Role.objects.get_or_create(code=code, defaults={"name": name})[0]

        r_rm = role("REGIONAL_MANAGER", "Regional Manager")
        r_ceo = role("CEO", "CEO")
        r_hr = role("HR_HO", "HR Directorate")
        r_sup = role("SUPERVISOR", "Supervisor/Unit Head")

        # Create approver users
        rm_user, _ = User.objects.get_or_create(username="rm", defaults={"email": "rm@gea.local"})
        rm_user.set_password("Pass@12345"); rm_user.save()
        UserRole.objects.get_or_create(user=rm_user, role=r_rm)

        ceo_user, _ = User.objects.get_or_create(username="ceo", defaults={"email": "ceo@gea.local"})
        ceo_user.set_password("Pass@12345"); ceo_user.save()
        UserRole.objects.get_or_create(user=ceo_user, role=r_ceo)

        hr_user, _ = User.objects.get_or_create(username="hr", defaults={"email": "hr@gea.local"})
        hr_user.set_password("Pass@12345"); hr_user.save()
        UserRole.objects.get_or_create(user=hr_user, role=r_hr)

        sup_user, _ = User.objects.get_or_create(username="sup", defaults={"email": "sup@gea.local"})
        sup_user.set_password("Pass@12345"); sup_user.save()
        UserRole.objects.get_or_create(user=sup_user, role=r_sup)

        # Create 3 employees (Junior/Senior/Supervisor) for leave tests
        def mk_emp(staff_no, fn, ln):
            emp, _ = Employee.objects.get_or_create(
                staff_no=staff_no,
                defaults={"first_name": fn, "last_name": ln, "email": f"{staff_no.lower()}@gea.local"},
            )
            return emp

        junior = mk_emp("J001", "Junior", "Officer")
        senior = mk_emp("S001", "Senior", "Officer")
        supervisor = mk_emp("SP001", "Supervisor", "Officer")

        # Connect employee user accounts (optional, but helpful)
        j_user, _ = User.objects.get_or_create(username="junior", defaults={"email": "junior@gea.local"})
        j_user.set_password("Pass@12345"); j_user.save()
        junior.user = j_user; junior.save()

        s_user, _ = User.objects.get_or_create(username="senior", defaults={"email": "senior@gea.local"})
        s_user.set_password("Pass@12345"); s_user.save()
        senior.user = s_user; senior.save()

        sp_user, _ = User.objects.get_or_create(username="supervisor", defaults={"email": "supervisor@gea.local"})
        sp_user.set_password("Pass@12345"); sp_user.save()
        supervisor.user = sp_user; supervisor.save()

        # Employment records (THIS drives workflow selection)
        today = date.today()
        Employment.objects.filter(employee=junior, status="ACTIVE").update(status="ENDED")
        Employment.objects.filter(employee=senior, status="ACTIVE").update(status="ENDED")
        Employment.objects.filter(employee=supervisor, status="ACTIVE").update(status="ENDED")

        Employment.objects.create(
            employee=junior, employment_type="PERMANENT", start_date=today,
            grade=grade, position=pos, region=region, department=dept,
            supervisor=supervisor, status="ACTIVE", staff_category="JUNIOR",
        )
        Employment.objects.create(
            employee=senior, employment_type="PERMANENT", start_date=today,
            grade=grade, position=pos, region=region, department=dept,
            supervisor=supervisor, status="ACTIVE", staff_category="SENIOR",
        )
        Employment.objects.create(
            employee=supervisor, employment_type="PERMANENT", start_date=today,
            grade=grade, position=pos, region=region, department=dept,
            supervisor=None, status="ACTIVE", staff_category="SUPERVISOR",
        )

        self.stdout.write(self.style.SUCCESS("✅ Demo users created: junior/senior/supervisor + rm/ceo/hr/sup (Pass@12345)"))
