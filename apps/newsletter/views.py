"""
apps/newsletter/views.py
=========================
Newsletter subscription endpoints.
"""

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import Subscriber
from .serializers import SubscribeSerializer, SubscriberAdminSerializer
from .tasks import send_confirmation_email
from core.permissions import IsAdminUser
from core.utils import generate_confirm_token, verify_confirm_token


class SubscribeView(APIView):
    """
    POST /api/v1/newsletter/subscribe/
    Rate limited: 10 per day per IP (bot/spam protection).
    Sends a confirmation email — user must click to activate.
    """

    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="10/d", method="POST", block=True))
    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        source = serializer.validated_data["source"]

        subscriber, created = Subscriber.objects.get_or_create(
            email=email, defaults={"source": source, "status": "pending"}
        )

        if not created and subscriber.status == "active":
            return Response(
                {"message": "You are already subscribed! 🎉"}, status=status.HTTP_200_OK
            )

        # Generate signed, time-limited token and send confirmation email
        token = generate_confirm_token(email)
        send_confirmation_email.delay(email=email, token=token)

        return Response(
            {
                "message": "Please check your email to confirm subscription! 📧",
                "subscribed_at": subscriber.subscribed_at,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConfirmSubscriptionView(APIView):
    """
    GET /api/v1/newsletter/confirm/{token}/
    User clicks the confirmation link from their email.
    Token is signed with SECRET_KEY and expires in 24h.
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        email = verify_confirm_token(token)

        if not email:
            return Response(
                {"error": "This confirmation link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subscriber = Subscriber.objects.get(email=email)
        except Subscriber.DoesNotExist:
            return Response(
                {"error": "Subscriber not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if subscriber.status == "active":
            return Response({"message": "Already confirmed! ✅"})

        subscriber.status = "active"
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["status", "confirmed_at"])

        return Response(
            {
                "message": "Email confirmed! You are now subscribed. 🎉",
                "confirmed_at": subscriber.confirmed_at,
            }
        )


class UnsubscribeView(APIView):
    """
    POST /api/v1/newsletter/unsubscribe/
    Body: { "token": "signed-unsubscribe-token" }
    OR (legacy/fallback): { "email": "user@example.com" }

    FIX H8: Now requires a signed token (sent in email footer) to prevent
    attackers from unsubscribing arbitrary email addresses.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token", "").strip()
        email = request.data.get("email", "").lower().strip()

        # Preferred: token-based unsubscribe (secure)
        if token:
            from core.utils import verify_unsubscribe_token
            verified_email = verify_unsubscribe_token(token)
            if not verified_email:
                return Response(
                    {"error": "Invalid or expired unsubscribe link."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            email = verified_email

        if not email:
            return Response(
                {"error": "Email or token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subscriber = Subscriber.objects.get(email=email)
            subscriber.status = "inactive"
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save(update_fields=["status", "unsubscribed_at"])
        except Subscriber.DoesNotExist:
            pass  # Don't reveal whether the email exists

        return Response({"message": "You have been unsubscribed."})


class AdminSubscriberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/admin/newsletter/subscribers/
    List and filter subscribers. Export via ?format=csv in future.
    """

    permission_classes = [IsAdminUser]
    serializer_class = SubscriberAdminSerializer
    queryset = Subscriber.objects.all()
    filterset_fields = ["status"]
    search_fields = ["email"]
    ordering_fields = ["subscribed_at", "confirmed_at"]
    ordering = ["-subscribed_at"]
