from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class OfferCreateRateThrottle(UserRateThrottle):
    """Limits how many offers a business user can publish."""

    scope = 'offer_create'

    def allow_request(self, request, view):
        # reading is covered by the default limits, only writing counts here
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class OfferUpdateRateThrottle(UserRateThrottle):
    """Limits edits and deletions of offers."""

    scope = 'offer_update'

    def allow_request(self, request, view):
        # reading is covered by the default limits, only writing counts here
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
