from django.db.models import Q
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile
from orders_app.models import Order

from .permissions import IsCustomer, IsBusinessUser, IsOrderProvider
from .serializers import OrderRetrieveWriteSerializer, OrderUpdateSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """Orders of the logged in user, on either side of the deal. Only customers may order."""

    serializer_class = OrderRetrieveWriteSerializer

    def get_queryset(self):
        # everyone sees only their own orders, as customer or as provider
        return Order.objects.filter(
            Q(customer_user=self.request.user) | Q(business_user=self.request.user)
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]
        # covers the safe methods and every verb without a handler, which then ends in 405
        return [IsAuthenticated()]


class OrderSingleUpdateDestroyView(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    """Status change by the provider, deletion by an admin. No GET and no PUT here."""

    lookup_url_kwarg = "id"
    serializer_class = OrderUpdateSerializer
    queryset = Order.objects.all()

    # the mixins bring update() and destroy(), the mapping to the verbs is ours
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsBusinessUser(), IsOrderProvider()]
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAdminUser()]
        # without this the preflight OPTIONS would crash instead of being answered
        return [IsAuthenticated()]


class OrderCountView(APIView):
    """Number of running orders of one provider. Plain APIView, the answer is a single number."""

    def get(self, request, *args, **kwargs):
        business_id = kwargs['business_user_id']
        # the id has to belong to a business profile, any other one would count to zero
        business_user = UserProfile.objects.filter(user_id=business_id, type="business").first()
        if business_user:
            count = Order.objects.filter(business_user=business_id, status="in_progress")
            return Response({"order_count": count.count()}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"Error": "No business user with this id."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CompletedOrderCountView(APIView):
    """Same as above for finished orders."""

    def get(self, request, *args, **kwargs):
        business_id = kwargs['business_user_id']
        business_user = UserProfile.objects.filter(user_id=business_id, type="business").first()
        if business_user:
            count = Order.objects.filter(business_user=business_id, status="completed")
            return Response({"completed_order_count": count.count()}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"Error": "No business user with this id."},
                status=status.HTTP_404_NOT_FOUND,
            )
