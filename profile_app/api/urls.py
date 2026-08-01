from django.urls import path
from .views import ProfileView, BusinessProfileView, CustomerProfileView


urlpatterns = [
    path('profile/<int:pk>/', ProfileView.as_view(), name='profil'),
    path('profile/business/', BusinessProfileView.as_view(), name='business_profile_list'),
    path('profile/customer/', CustomerProfileView.as_view(), name='customer_profile_list')
]