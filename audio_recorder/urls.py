# audio_recorder/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recorder.urls')),  # Include recorder URLs
    # Redirect /academic/results/ to home page
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)