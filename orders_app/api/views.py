from rest_framework import generics, mixins
from orders_app.models import Order
from .serializers import OrderRetrieveWriteSerializer, OrderUpdateSerializer
from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, IsAdminUser
from .permissions import IsCustomer, IsBusinessUser


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderRetrieveWriteSerializer


    def get_queryset(self):
        return Order.objects.filter(Q(customer_user=self.request.user) | Q(business_user=self.request.user))

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]


class OrderSingleUpdateDestroyView(
    mixins.UpdateModelMixin, 
    mixins.DestroyModelMixin, 
    generics.GenericAPIView):

    lookup_url_kwarg = "id"
    serializer_class = OrderUpdateSerializer
    queryset = Order.objects.all()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsBusinessUser()]
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAdminUser()]

        