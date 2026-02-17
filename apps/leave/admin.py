from django.contrib import admin

# Register your models here.
from django.contrib import admin
from apps.leave.models import LeaveRequest

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "status", "created_at")
    list_filter = ("leave_type", "status")
