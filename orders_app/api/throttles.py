from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class OrderCreateRateThrottle(UserRateThrottle):
    """Limits how many orders a customer can place."""

    scope = 'order_create'

    def allow_request(self, request, view):
        """Count only writing requests; reads fall under the default limits."""
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class OrderUpdateRateThrottle(UserRateThrottle):
    """Limits status changes and deletions of orders."""

    scope = 'order_update'

    def allow_request(self, request, view):
        """Count only writing requests; reads fall under the default limits."""
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
