from django.contrib import admin

# Register your models here.
from django.contrib import admin
from apps.documents.models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("owner_type", "doc_type", "title", "uploaded_by", "created_at")
    list_filter = ("owner_type", "doc_type", "access_scope")
