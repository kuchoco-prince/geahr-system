from django.contrib import admin

# Register your models here.
from django.contrib import admin
from apps.audit.models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("action", "entity_type")
