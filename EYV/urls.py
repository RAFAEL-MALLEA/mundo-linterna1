"""Rutas principales del proyecto EYV."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('SeguridadAdministrativa/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('appEYV.urls')),
]

# Los archivos subidos (imágenes de productos) se sirven solo en desarrollo.
# En producción deben servirse desde el servidor web (nginx, etc.).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
