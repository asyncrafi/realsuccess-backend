import logging
from django.core.cache import cache
from django.utils import timezone
from apps.events.models import Event
from apps.tickets.models import Ticket

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Extract client IP address from request headers or remote addr.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def resolve_event(request, access_code=None, event_id=None, email=None):
    """
    Resolves the targeted Event object using multiple fallback strategies:
    1. Explicit access_code or event_id parameters.
    2. request.data or request.query_params.
    3. Pending event ID cached for the email (if provided).
    4. Last event access code or ID cached for the client IP.
    5. Currently Active event or nearest upcoming event.
    """
    # 1. Explicit parameters
    if access_code:
        event = Event.objects.filter(access_code__iexact=str(access_code).strip()).first()
        if event:
            return event

    if event_id:
        try:
            event = Event.objects.filter(id=int(event_id)).first()
            if event:
                return event
        except (ValueError, TypeError):
            pass

    # 2. From request payload / query params
    if request:
        req_code = (
            request.data.get("access_code")
            or request.data.get("event_access_code")
            or request.query_params.get("access_code")
        )
        if req_code:
            event = Event.objects.filter(access_code__iexact=str(req_code).strip()).first()
            if event:
                return event

        req_eid = (
            request.data.get("event_id")
            or request.query_params.get("event_id")
        )
        if req_eid:
            try:
                event = Event.objects.filter(id=int(req_eid)).first()
                if event:
                    return event
            except (ValueError, TypeError):
                pass

    # 3. From email pending cache
    if email:
        norm_email = email.strip().lower()
        cached_eid = cache.get(f"pending_event_{norm_email}")
        if cached_eid:
            try:
                event = Event.objects.filter(id=int(cached_eid)).first()
                if event:
                    return event
            except (ValueError, TypeError):
                pass

    # 4. From client IP cache
    client_ip = get_client_ip(request)
    if client_ip:
        cached_code = cache.get(f"last_event_code_{client_ip}")
        if cached_code:
            event = Event.objects.filter(access_code__iexact=str(cached_code).strip()).first()
            if event:
                return event

        cached_eid = cache.get(f"last_event_id_{client_ip}")
        if cached_eid:
            try:
                event = Event.objects.filter(id=int(cached_eid)).first()
                if event:
                    return event
            except (ValueError, TypeError):
                pass

    # 5. Default fallback to Active event or nearest event
    event = Event.objects.filter(status="Active").first()
    if not event:
        event = Event.objects.filter(start_date__gte=timezone.localdate()).order_by("start_date").first()
    if not event:
        event = Event.objects.order_by("-start_date").first()

    return event


def is_user_verified_for_event(email, event, user=None):
    """
    Checks if a user has already completed OTP verification or holds a confirmed
    registration for the specified event.
    """
    if not event or not email:
        return False

    norm_email = email.strip().lower()

    # 1. Fast cache check
    if cache.get(f"event_verified_{event.id}_{norm_email}"):
        return True

    # 2. Check Ticket model for Confirmed registration on this event
    ticket_query = Ticket.objects.filter(
        event=event,
        registration_status="Confirmed"
    )

    if ticket_query.filter(attendee_email__iexact=norm_email).exists():
        # Populate cache
        cache.set(f"event_verified_{event.id}_{norm_email}", True, timeout=86400 * 30)
        return True

    if user and ticket_query.filter(user=user).exists():
        cache.set(f"event_verified_{event.id}_{norm_email}", True, timeout=86400 * 30)
        return True

    return False


def mark_user_verified_for_event(email, event, user=None):
    """
    Marks the user as verified for the event:
    1. Sets persistent cache flag for 30 days.
    2. Ensures a Confirmed Ticket exists for the user and event.
    """
    if not event or not email:
        return None

    norm_email = email.strip().lower()

    # Cache verification flag
    cache.set(f"event_verified_{event.id}_{norm_email}", True, timeout=86400 * 30)
    cache.delete(f"pending_event_{norm_email}")

    # Ensure Confirmed Ticket exists
    ticket = Ticket.objects.filter(event=event, attendee_email__iexact=norm_email).first()
    if not ticket and user:
        ticket = Ticket.objects.filter(event=event, user=user).first()

    if ticket:
        ticket.registration_status = "Confirmed"
        if user and not ticket.user:
            ticket.user = user
        ticket.save()
    else:
        name = ""
        if user and hasattr(user, "profile") and user.profile and getattr(user.profile, "name", None):
            name = user.profile.name
        else:
            name = norm_email.split("@")[0].replace(".", " ").capitalize()

        ticket = Ticket.objects.create(
            event=event,
            user=user if user else None,
            attendee_name=name,
            attendee_email=norm_email,
            ticket_type="General",
            registration_status="Confirmed",
            access_code=event.access_code,
        )

    return ticket
