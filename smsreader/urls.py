from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Import settings to access STATIC_URL and MEDIA_URL
from django.conf.urls.static import static  # Import static helper function to serve static and media files

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('', include('transactions.urls')),  # Include all URLs from transactions app
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
