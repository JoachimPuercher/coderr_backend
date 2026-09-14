from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class ReviewCreateRateThrottle(UserRateThrottle):
    """Limits how many reviews a customer can write."""

    scope = 'review_create'

    def allow_request(self, request, view):
        # reading is covered by the default limits, only writing counts here
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class ReviewUpdateRateThrottle(UserRateThrottle):
    """Limits edits and deletions of reviews."""

    scope = 'review_update'

    def allow_request(self, request, view):
        # reading is covered by the default limits, only writing counts here
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
