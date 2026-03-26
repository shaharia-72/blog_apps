"""
core/exceptions.py
===================
Custom DRF exception handler.
Referenced in settings: EXCEPTION_HANDLER = 'core.exceptions.custom_exception_handler'
Returns consistent JSON error shapes for ALL error types.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Unified error response shape:
    {
        "error": true,
        "code": "not_found",
        "message": "No Blog matches the given query.",
        "details": {...}   ← only on validation errors
    }
    """
    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': True,
            'code': _get_error_code(exc),
            'message': _get_message(response.data),
        }
        if response.status_code == 400:
            error_data['details'] = response.data
        response.data = error_data
        return response

    # Handle Django's own exceptions
    if isinstance(exc, Http404):
        return Response(
            {'error': True, 'code': 'not_found', 'message': str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {'error': True, 'code': 'permission_denied', 'message': 'Permission denied.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Unexpected errors — log and return 500
    logger.exception('Unhandled exception in %s: %s', context.get('view'), exc)
    return Response(
        {'error': True, 'code': 'server_error', 'message': 'An unexpected error occurred.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_code(exc):
    code_map = {
        'AuthenticationFailed': 'auth_failed',
        'NotAuthenticated': 'not_authenticated',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'MethodNotAllowed': 'method_not_allowed',
        'Throttled': 'rate_limit_exceeded',
        'ValidationError': 'validation_error',
        'ParseError': 'parse_error',
    }
    return code_map.get(type(exc).__name__, 'error')


def _get_message(data):
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, dict):
        for key in ('detail', 'non_field_errors', 'message'):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        # Return first field error
        first_key = next(iter(data))
        val = data[first_key]
        return f"{first_key}: {val[0] if isinstance(val, list) else val}"
    return str(data)
