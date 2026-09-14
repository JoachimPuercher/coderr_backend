from rest_framework.throttling import UserRateThrottle


class BaseInfoRateThrottle(UserRateThrottle):
    """The figures are aggregated on every call,
    so the public endpoint gets its own limit.
    """

    scope = 'base_info'
