from rest_framework import generics, mixins
from reviews_app.models import Review
from .serializers import ReviewSerializer, ReviewUpdateSerializer
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import ReviewFilter
from orders_app.api.permissions import IsCustomer
from .permissions import IsReviewOwner

class ReviewListCreateView(generics.ListCreateAPIView):

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]


class ReviewUpdateDestroyView(
    mixins.UpdateModelMixin, 
    mixins.DestroyModelMixin, 
    generics.GenericAPIView):

    lookup_url_kwarg = "id"
    serializer_class = ReviewUpdateSerializer
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated, IsReviewOwner]

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)