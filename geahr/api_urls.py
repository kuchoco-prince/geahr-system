from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.leave.api import LeaveRequestViewSet
from apps.workflows.api import ApprovalRequestViewSet
from apps.documents.api import DocumentViewSet
from apps.accounts.api import token_obtain_pair, token_refresh

router = DefaultRouter()
router.register(r"leave/requests", LeaveRequestViewSet, basename="leave-requests")
router.register(r"approvals/requests", ApprovalRequestViewSet, basename="approvals-requests")
router.register(r"documents", DocumentViewSet, basename="documents")

urlpatterns = [
    path("auth/token/", token_obtain_pair),
    path("auth/refresh/", token_refresh),
    path("", include(router.urls)),
]

