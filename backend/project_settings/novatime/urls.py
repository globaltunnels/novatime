"""
URL configuration for NovaTime project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health checks
    path('health/', include('health_check.urls')),

    # Authentication
    path('accounts/', include('allauth.urls')),
    path('auth/', include('apps.accounts.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # API v1
    path('api/v1/', include([
        path('tasks/', include('apps.tasks-app.urls')),
        path('assignments/', include('apps.tasks-app.urls')),  # Assignments are part of tasks
        path('time-entries/', include('apps.time-entries-app.urls')),
        path('timesheets/', include('apps.timesheets-app.urls')),
        path('approvals/', include('apps.approvals-app.urls')),
        path('attendance/', include('apps.attendance-app.urls')),
        path('projects/', include('apps.projects-app.urls')),
        path('billing/', include('apps.billing-app.urls')),
        path('conversations/', include('apps.conversations-app.urls')),
        path('messages/', include('apps.conversations-app.urls')),  # Messages are part of conversations
        path('ai/', include('apps.ai-app.urls')),
        path('insights/', include('apps.insights-app.urls')),
        path('integrations/', include('apps.integrations-app.urls')),
        path('seo/', include('apps.seo-app.urls')),
        path('abtests/', include('apps.abtests-app.urls')),
    ])),

    # Organizations
    path('orgs/', include('apps.organizations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)