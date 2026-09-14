from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from orders_app.api.permissions import IsCustomer
from reviews_app.models import Review

from .filters import ReviewFilter
from .permissions import IsReviewOwner
from .serializers import ReviewSerializer, ReviewUpdateSerializer
from .throttles import ReviewCreateRateThrottle, ReviewUpdateRateThrottle


class ReviewListCreateView(generics.ListCreateAPIView):
    """Review list, filterable by user. Only customers may write one."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]
    throttle_classes = [UserRateThrottle, ReviewCreateRateThrottle]

    def perform_create(self, serializer):
        """Store the requesting user as author of the new review."""
        # the author comes from the token, the
        # payload must not decide who reviews
        serializer.save(reviewer=self.request.user)

    def get_permissions(self):
        """Every logged in user may read, only customers may write."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]
        # covers the safe methods and every verb
        # without a handler, which then ends in 405
        return [IsAuthenticated()]


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
    throttle_classes = [UserRateThrottle, ReviewUpdateRateThrottle]

    # the mixins bring update() and destroy(), the mapping to the verbs is ours
    def patch(self, request, *args, **kwargs):
        """Edit rating or description, always as a partial update."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the review; the permission limits this to its author."""
        return self.destroy(request, *args, **kwargs)
