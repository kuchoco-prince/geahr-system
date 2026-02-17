from rest_framework import serializers, viewsets
from rest_framework.parsers import MultiPartParser, FormParser

from apps.documents.models import Document
from apps.accounts.permissions import IsHROrManagement
from apps.audit.services import write_audit


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ("uploaded_by", "created_at", "updated_at")


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Upload and manage documents (letters, attachments, scanned docs, HR files).
    Supports multipart file upload.
    """
    queryset = Document.objects.all().order_by("-created_at")
    serializer_class = DocumentSerializer
    permission_classes = [IsHROrManagement]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        obj = serializer.save(uploaded_by=self.request.user)
        write_audit("CREATE", "Document", obj.id, before=None, after=DocumentSerializer(obj).data)

    def perform_update(self, serializer):
        before = DocumentSerializer(self.get_object()).data
        obj = serializer.save()
        write_audit("UPDATE", "Document", obj.id, before=before, after=DocumentSerializer(obj).data)
