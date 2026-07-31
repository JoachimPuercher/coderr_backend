from django.urls import path, include
from .views import ProfileView


urlpatterns = [
    path('profile/<int:pk>/', ProfileView.as_view(), name='registration'),
]