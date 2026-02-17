from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "ok": True,
        "message": "GEA HR Backend is running",
        "api_root": "/api/"
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("geahr.api_urls")),
    path("", home),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
