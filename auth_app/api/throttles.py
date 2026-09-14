from rest_framework.throttling import UserRateThrottle


class RegistrationRateThrottle(UserRateThrottle):
    """Keeps a single client from creating accounts in bulk.

    Registration happens before a token exists, so the counter runs per IP address.
    """

    scope = 'registration'


class LoginRateThrottle(UserRateThrottle):
    """Slows down password guessing against the login, counted per IP address."""

    scope = 'login'
