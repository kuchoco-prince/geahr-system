from django.db import models
from django.conf import settings

from apps.common.models import UUIDModel, TimeStampedModel
from apps.org.models import Region, Department, Position, Grade


class Employee(UUIDModel, TimeStampedModel):
    """
    Core employee profile record.
    One employee may have multiple employment records over time.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        EXITED = "EXITED", "Exited"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employee"
    )

    staff_no = models.CharField(max_length=50, unique=True, db_index=True)

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    other_names = models.CharField(max_length=120, blank=True)

    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    def __str__(self):
        return f"{self.staff_no} - {self.first_name} {self.last_name}"


class Employment(UUIDModel, TimeStampedModel):
    """
    Represents a specific employment record (position, grade, region etc.)
    This drives workflow selection (staff_category).
    """

    class EmploymentType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent"
        CONTRACT = "CONTRACT", "Contract"
        NSS = "NSS", "National Service"
        SECONDMENT = "SECONDMENT", "Secondment"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ENDED = "ENDED", "Ended"

    # 🔥 THIS DRIVES GEA LEAVE WORKFLOW SELECTION
    class StaffCategory(models.TextChoices):
        JUNIOR = "JUNIOR", "Junior Officer (Regional)"
        SENIOR = "SENIOR", "Senior Officer"
        SUPERVISOR = "SUPERVISOR", "Supervisor (RM/Director/Unit Head)"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employments"
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices
    )

    # ✅ Added staff_category (REQUIRED for leave routing)
    staff_category = models.CharField(
        max_length=20,
        choices=StaffCategory.choices,
        db_index=True,
        default=StaffCategory.SENIOR
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    grade = models.ForeignKey(Grade, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)

    supervisor = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="supervisees"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        indexes = [
            models.Index(fields=["region", "department"]),
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["staff_category"]),
        ]

    def __str__(self):
        return f"{self.employee.staff_no} - {self.position.title} ({self.staff_category})"
