from django.urls import path
from .views import OrderListCreateView, OrderSingleUpdateDestroyView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name="order"),
    path('orders/<int:id>/', OrderSingleUpdateDestroyView.as_view(), name="single_order")
]