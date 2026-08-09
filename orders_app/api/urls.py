from django.urls import path

from .views import (
    OrderListCreateView,
    OrderSingleUpdateDestroyView,
    OrderCountView,
    CompletedOrderCountView,
)


urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order'),
    path('orders/<int:id>/', OrderSingleUpdateDestroyView.as_view(), name='single_order'),
    path('order-count/<int:business_user_id>/', OrderCountView.as_view(), name='order_count'),
    path(
        'completed-order-count/<int:business_user_id>/',
        CompletedOrderCountView.as_view(),
        name='completed_order_count',
    ),
]
