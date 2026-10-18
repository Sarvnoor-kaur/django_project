from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (login / logout) – use Django’s built‑in views
    path('accounts/', include('django.contrib.auth.urls')),

    # Local apps
    path('accounts/', include('accounts.urls')),
    path('learning/', include('learning.urls', namespace='learning')),
    path('', include('core.urls')),          # core handles home, dashboard, etc.

    # Catch‑all for the root – redirect to home if someone lands on "/"
    path('', RedirectView.as_view(pattern_name='home', permanent=False)),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Custom error handlers
handler403 = 'core.views.handler403'
handler404 = 'core.views.handler404'
