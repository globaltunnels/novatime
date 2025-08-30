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
# from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView  # Temporarily disabled

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API documentation (temporarily disabled)
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health checks
    path('health/', include('health_check.urls')),

    # Authentication (temporarily disabled)
    # path('accounts/', include('allauth.urls')),
    # path('api/v1/auth/', include('iam.urls')),  # Enable IAM URLs
    # path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # API v1 - Individual modules (temporarily disabled)
    # path('api/v1/timesheets/', include('timesheets.urls')),
    # path('api/v1/projects/', include('projects.urls')),
    # path('api/v1/ai/', include('ai_services.urls')),

    # API v1 (temporarily disabled for initial setup)
    # path('api/v1/', include([
    #     path('accounts/', include('iam.urls')),
    #     path('organizations/', include('organizations.urls')),
    #     path('tasks/', include('tasks.urls')),
    #     path('assignments/', include('tasks.urls')),  # Assignments are part of tasks
    #     path('time-entries/', include('time_entries.urls')),
    #     path('timesheets/', include('timesheets.urls')),
    #     path('approvals/', include('approvals.urls')),
    #     path('attendance/', include('attendance.urls')),
    #     path('projects/', include('projects.urls')),
    #     path('billing/', include('billing.urls')),
    #     path('conversations/', include('conversations.urls')),
    #     path('messages/', include('conversations.urls')),  # Messages are part of conversations
    #     path('ai/', include('ai.urls')),
    #     path('insights/', include('insights.urls')),
    #     path('integrations/', include('integrations.urls')),
    #     path('seo/', include('seo.urls')),
    #     path('abtests/', include('abtests.urls')),
    # ])),

    # Organizations (temporarily disabled)
    # path('orgs/', include('organizations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)