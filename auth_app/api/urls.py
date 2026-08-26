# ORIGINAL

# from django.urls import path

# from .views import RegistrationView, LoginView


# urlpatterns = [
#     path('registration/', RegistrationView.as_view(), name='registration'),
#     path('login/', LoginView.as_view(), name='login'),
# ]


# JWT TESTING
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CookieTokenObtainPairView
from .views import RegistrationView, LoginView


urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]




