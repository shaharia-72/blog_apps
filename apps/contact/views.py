"""
apps/contact/views.py
======================
Contact form submission and admin message management.
"""

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import ContactMessage
from .serializers import ContactFormSerializer, ContactMessageAdminSerializer
from .tasks import notify_admin_new_contact
from core.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema(tags=["Blog"])
class ContactView(APIView):
    """
    POST /api/v1/contact/
    Rate limited: 5 per hour per IP — stops form spam.
    Honeypot field checked in serializer — bots rejected silently.
    Sends admin notification email asynchronously via Celery.
    """

    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/h", method="POST", block=True))
    def post(self, request):
        serializer = ContactFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        msg = ContactMessage.objects.create(
            name=d["name"],
            email=d["email"],
            subject=d["subject"],
            message=d["message"],
            company=d["company"],
            budget=d["budget"],
            project_type=d["project_type"],
            utm_source=request.data.get("utm_source", ""),
        )

        # Fire and forget — don't make the user wait for email to send
        notify_admin_new_contact.delay(msg.id)

        return Response(
            {
                "id": msg.id,
                "message": "Thanks! I'll get back to you within 24 hours. 🚀",
                "submitted_at": msg.submitted_at,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(tags=["Admin"]),
    retrieve=extend_schema(tags=["Admin"]),
    partial_update=extend_schema(tags=["Admin"]),
    destroy=extend_schema(tags=["Admin"]),
)
class AdminContactViewSet(viewsets.ModelViewSet):
    """
    Admin contact inbox.

    GET    /api/v1/admin/contact/       → All messages (filter by ?status=new)
    GET    /api/v1/admin/contact/{id}/  → Message detail
    PATCH  /api/v1/admin/contact/{id}/  → Update status and admin notes
    DELETE /api/v1/admin/contact/{id}/  → Delete message
    """

    permission_classes = [IsAdminUser]
    serializer_class = ContactMessageAdminSerializer
    queryset = ContactMessage.objects.all()
    filterset_fields = ["status"]
    search_fields = ["name", "email", "subject", "message"]
    ordering_fields = ["submitted_at", "status"]
    ordering = ["-submitted_at"]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def partial_update(self, request, *args, **kwargs):
        """Auto-set replied_at timestamp when marking status = 'replied'."""
        msg = self.get_object()
        if request.data.get("status") == "replied" and not msg.replied_at:
            # Merge replied_at into request data before saving
            data = request.data.copy()
            data["replied_at"] = timezone.now()
            serializer = self.get_serializer(msg, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return super().partial_update(request, *args, **kwargs)
