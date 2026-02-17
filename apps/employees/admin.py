from django.contrib import admin

# Register your models here.
from django.contrib import admin
from apps.employees.models import Employee, Employment

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("staff_no", "first_name", "last_name", "status")
    search_fields = ("staff_no", "first_name", "last_name", "email")

@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ("employee", "employment_type", "staff_category", "region", "department", "status", "start_date")
    list_filter = ("staff_category", "region", "status", "employment_type")
