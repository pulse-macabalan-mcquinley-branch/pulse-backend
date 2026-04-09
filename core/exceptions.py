import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Replace DRF's default exception handler with a structured format.
    Called automatically via REST_FRAMEWORK['EXCEPTION_HANDLER'].
    """
    # Convert Django native exceptions to DRF equivalents
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=exc.message_dict
                                        if hasattr(exc, "message_dict")
                                        else exc.messages)
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = exception_handler(exc, context)

    if response is not None:
        errors = _extract_errors(exc, response)
        response.data = {
            "errors": errors,
            "status_code": response.status_code,
        }
        return response

    # Unhandled exceptions → 500
    logger.exception("Unhandled server error", exc_info=exc)
    return Response(
        {
            "errors": [
                {"code": "server_error", "detail": "An unexpected error occurred.", "attr": None}
            ],
            "status_code": 500,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_errors(exc, response):
    errors = []
    if hasattr(exc, "detail"):
        _parse_detail(exc.detail, errors)
    return errors


def _parse_detail(detail, errors, attr=None):
    if isinstance(detail, list):
        for item in detail:
            _parse_detail(item, errors, attr)
    elif isinstance(detail, dict):
        for field, value in detail.items():
            _parse_detail(value, errors, attr=field)
    elif isinstance(detail, exceptions.ErrorDetail):
        errors.append({
            "code": detail.code,
            "detail": str(detail),
            "attr": attr,
        })
    else:
        errors.append({"code": "error", "detail": str(detail), "attr": attr})


# ── Typed application exceptions ──────────────────────────────
class ApplicationError(exceptions.APIException):
    """Base class for all custom application errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Application error."
    default_code = "application_error"


class ResourceNotFound(exceptions.NotFound):
    """404 with a resource-specific message."""
    def __init__(self, resource="Resource"):
        super().__init__(detail=f"{resource} not found.")


class PermissionDenied(exceptions.PermissionDenied):
    """403 raised when RBAC check fails."""
    pass


class ConflictError(ApplicationError):
    """409 — resource already exists."""
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


class ServiceUnavailable(exceptions.APIException):
    """503 — upstream dependency is down."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "service_unavailable"
    default_detail = "Service temporarily unavailable."