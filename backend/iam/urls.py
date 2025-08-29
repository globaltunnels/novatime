from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    AuthViewSet,
    UserProfileView,
    ChangePasswordView
)

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')

urlpatterns = [
    # JWT Authentication
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Router URLs
    path('', include(router.urls)),
]