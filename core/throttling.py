from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Short-window rate limit to prevent spikes. Default: 60/min."""
    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """Long-window rate limit to prevent abuse. Default: 1000/day."""
    scope = "sustained"


class AnonBurstThrottle(AnonRateThrottle):
    """Unauthenticated burst rate. Default: 20/min."""
    scope = "anon"

class AnonSustainedThrottle(AnonRateThrottle):
    scope = "anon_sustained"

class AdminBypassThrottle(UserRateThrottle):
    """
    Admin users bypass throttling entirely.
    Apply to admin-only ViewSets via throttle_classes.
    """

    scope = "burst"

    def allow_request(self, request, view):
        if request.user.is_authenticated and request.user.is_staff:
            return True
        return super().allow_request(request, view)


class SensitiveEndpointThrottle(UserRateThrottle):
    """
    Very strict throttle for sensitive actions like password reset.
    Add to REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']:
        'sensitive': '5/hour'
    """

    scope = "sensitive"