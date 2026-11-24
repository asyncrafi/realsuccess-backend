from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import Ticket
from .serializers import TicketSerializer, AttendeeSerializer, MyTicketDetailSerializer


class TicketListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "ticket_type", "registration_status", "check_in_status"]
    search_fields = ["ticket_id", "attendee_name", "attendee_email", "event__name", "seat_no"]
    ordering_fields = ["created_at", "issue_date", "attendee_name"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return self.created_response(data=self.get_serializer(ticket).data, message="Ticket issued successfully")


class TicketDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data, message="Ticket updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Ticket deleted successfully")


class TicketCheckInView(BaseResponseMixin, generics.GenericAPIView):
    """
    Check-in an attendee by ticket ID or QR code data.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        if pk:
            ticket = get_object_or_404(Ticket, pk=pk)
        else:
            ticket_id = request.data.get("ticket_id")
            ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

        ticket.check_in()
        return self.success_response(
            data=TicketSerializer(ticket).data,
            message=f"Attendee {ticket.attendee_name} successfully checked in!"
        )


class MyTicketView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile My Event Ticket screen:
    Retrieves the ticket for the authenticated user, or via access_code / email.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ticket = None
        if request.user.is_authenticated:
            ticket = Ticket.objects.filter(user=request.user).first()
            if not ticket:
                ticket = Ticket.objects.filter(attendee_email=request.user.email).first()

        if not ticket:
            access_code = request.query_params.get("access_code")
            email = request.query_params.get("email")
            if access_code:
                ticket = Ticket.objects.filter(access_code=access_code).first()
            elif email:
                ticket = Ticket.objects.filter(attendee_email=email).first()

        if not ticket:
            ticket = Ticket.objects.first()

        if not ticket:
            return self.not_found_response(message="No ticket found for this account.")

        serializer = MyTicketDetailSerializer(ticket)
        return self.success_response(data=serializer.data, message="My ticket retrieved successfully")


class AttendeeListView(BaseResponseMixin, generics.ListAPIView):
    """
    Admin Dashboard Attendee Management endpoint
    """
    queryset = Ticket.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "ticket_type", "registration_status", "check_in_status"]
    search_fields = ["attendee_name", "attendee_email", "access_code", "event__name", "attendee_phone"]
    ordering_fields = ["created_at", "attendee_name"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)


class AttendeeDetailView(BaseResponseMixin, generics.RetrieveUpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)
