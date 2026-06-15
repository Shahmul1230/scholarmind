from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path


def react_app(request):
    index_path = Path(settings.BASE_DIR) / "static" / "frontend" / "index.html"

    if index_path.exists():
        return FileResponse(
            open(index_path, "rb"),
            content_type="text/html"
        )

    return HttpResponse(
        "Frontend build not found. Build the frontend first.",
        status=501
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("papers.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r"^(?!api/|admin/|static/|media/).*$", react_app),
]