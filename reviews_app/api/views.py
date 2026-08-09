from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from orders_app.api.permissions import IsCustomer
from reviews_app.models import Review

from .filters import ReviewFilter
from .permissions import IsReviewOwner
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """Review list, filterable by user. Only customers may write one."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]

    def perform_create(self, serializer):
        # the author comes from the token, the payload must not decide who reviews
        serializer.save(reviewer=self.request.user)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]


class ReviewUpdateDestroyView(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    """Edit or delete a single review, author only. No GET and no PUT here."""

    lookup_url_kwarg = "id"
    serializer_class = ReviewUpdateSerializer
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated, IsReviewOwner]

    # the mixins bring update() and destroy(), the mapping to the verbs is ours
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
