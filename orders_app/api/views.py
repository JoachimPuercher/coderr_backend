from rest_framework import generics
from orders_app.models import Order
from .serializers import OrderRetrieveWriteSerializer
from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from .permissions import IsCustomer


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderRetrieveWriteSerializer


    def get_queryset(self):
        return Order.objects.filter(Q(customer_user=self.request.user) | Q(business_user=self.request.user))

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]