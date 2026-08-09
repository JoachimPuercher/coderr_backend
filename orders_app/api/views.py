from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from orders_app.models import Order
from .serializers import OrderRetrieveWriteSerializer, OrderUpdateSerializer
from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, IsAdminUser
from .permissions import IsCustomer, IsBusinessUser
from django.contrib.auth.models import User

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


class OrderCountView(APIView):

    def get(self, request, *args, **kwargs):
        business_id = kwargs['business_user_id']
        business_user = User.objects.filter(pk=business_id).first()
        if business_user:
            count = Order.objects.filter(business_user=business_id, status="in_progress")
            return Response({"order_count" : count.count()}, status=status.HTTP_200_OK)
        else:
            return Response({"Error" : "No business user with this id."}, status=status.HTTP_404_NOT_FOUND)

class CompletedOrderCountView(APIView):

    def get(self, request, *args, **kwargs):
        business_id = kwargs['business_user_id']
        business_user = User.objects.filter(pk=business_id).first()
        if business_user:
            count = Order.objects.filter(business_user=business_id, status="completed")
            return Response({"completed_order_count" : count.count()}, status=status.HTTP_200_OK)
        else:
            return Response({"Error" : "No business user with this id."}, status=status.HTTP_404_NOT_FOUND)