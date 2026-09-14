from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class ProfileUpdateRateThrottle(UserRateThrottle):
    """Limits how often a user can edit a profile."""

    scope = 'profile_update'

    def allow_request(self, request, view):
        """Count only writing requests; reads fall under the default limits."""
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
