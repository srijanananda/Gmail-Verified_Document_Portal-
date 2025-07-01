from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .jwt_views import MyTokenObtainPairView
from .views import home_view


urlpatterns = [
    # Auth Flow
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    

    # JWT
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/protected/', views.protected_api_view),

    # Forgot Password Flow
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp_view, name='verify_reset_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('', home_view, name='home'),

]
