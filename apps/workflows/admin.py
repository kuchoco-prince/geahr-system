from django.contrib import admin

# Register your models here.
from django.contrib import admin
from apps.workflows.models import WorkflowDefinition, WorkflowStep, ApprovalRequest, ApprovalAction

class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0

@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ("module", "code", "name", "region", "is_active")
    inlines = [WorkflowStepInline]

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("module", "request_type", "status", "current_step_order", "created_at")
    list_filter = ("module", "request_type", "status")

@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ("request", "step_order", "action", "actor", "created_at")
