from django.urls import path

from .views import ReviewListCreateView, ReviewUpdateDestroyView


urlpatterns = [
    path('reviews/', ReviewListCreateView.as_view(), name='reviews'),
    path('reviews/<int:id>/', ReviewUpdateDestroyView.as_view(), name='single_review'),
]
