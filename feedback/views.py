from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import generics, permissions
from feedback.permission import IsTicketOwnerOrAdmin
from .models import FeedbackTicket, TicketMessage
from .serializers import FeedbackTicketSerializer, TicketMessageSerializer


def is_admin(user):
    return getattr(user, "role", "") == "admin"


def is_sub_admin(user):
    return getattr(user, "role", "") == "subAdmin"


class FeedbackTicketListCreateView(APIView):
    @swagger_auto_schema(
        operation_summary="List Feedback Tickets",
        operation_description="Returns all tickets for admins/subadmins, or only user's own tickets for regular users",
        responses={
            200: FeedbackTicketSerializer(many=True),
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def get(self, request):
        user = request.user
        if user.is_superuser or is_admin(user) or is_sub_admin(user):
            tickets = FeedbackTicket.objects.all()
        else:
            tickets = FeedbackTicket.objects.filter(created_by=user)
        serializer = FeedbackTicketSerializer(tickets, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Feedback Ticket",
        operation_description="Create a new feedback ticket",
        request_body=FeedbackTicketSerializer,
        responses={
            201: FeedbackTicketSerializer,
            400: "Bad Request",
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def post(self, request):
        serializer = FeedbackTicketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackTicketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            ticket = FeedbackTicket.objects.get(pk=pk)
            if (
                user.is_superuser
                or is_admin(user)
                or is_sub_admin(user)
                or ticket.created_by == user
            ):
                return ticket
            return None
        except FeedbackTicket.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="Get Feedback Ticket Detail",
        operation_description="Retrieve details of a specific feedback ticket",
        responses={
            200: FeedbackTicketSerializer,
            404: "Not found or no permission",
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def get(self, request, pk):
        ticket = self.get_object(pk, request.user)
        if not ticket:
            return Response(
                {"error": "Not found or no permission."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = FeedbackTicketSerializer(ticket)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Update Feedback Ticket",
        operation_description="Update an existing feedback ticket. Users can only update their own tickets.",
        request_body=FeedbackTicketSerializer,
        responses={
            200: FeedbackTicketSerializer,
            400: "Bad Request",
            403: "Forbidden - Can only update own tickets",
            404: "Not found or no permission",
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def put(self, request, pk):
        ticket = self.get_object(pk, request.user)
        if not ticket:
            return Response(
                {"error": "Not found or no permission."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if ticket.created_by != request.user:
            return Response(
                {"error": "You can only update your own ticket."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = FeedbackTicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete Feedback Ticket",
        operation_description="Delete a feedback ticket. Users can only delete their own tickets.",
        responses={
            204: "No Content - Successfully deleted",
            403: "Forbidden - Can only delete own tickets",
            404: "Not found or no permission",
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def delete(self, request, pk):
        ticket = self.get_object(pk, request.user)
        if not ticket:
            return Response(
                {"error": "Not found or no permission."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if ticket.created_by != request.user:
            return Response(
                {"error": "You can only delete your own ticket."},
                status=status.HTTP_403_FORBIDDEN,
            )
        ticket.delete()
        return Response(
            {"message": "Ticket deleted."}, status=status.HTTP_204_NO_CONTENT
        )


class UserTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get User's Tickets",
        operation_description="Returns a list of all feedback tickets created by the authenticated user",
        responses={
            200: FeedbackTicketSerializer(many=True),
            401: "Authentication credentials were not provided.",
        },
        tags=["Feedback Tickets"],
    )
    def get(self, request):
        """
        Endpoint for users to view all their tickets
        """
        tickets = FeedbackTicket.objects.filter(created_by=request.user)
        serializer = FeedbackTicketSerializer(tickets, many=True)
        return Response(serializer.data)


class TicketChatAPIView(generics.ListCreateAPIView):
    serializer_class = TicketMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrAdmin]

    def get_queryset(self):
        """
        Return messages only for the specific ticket ID in the URL.
        Also validates that the user is allowed to see this ticket.
        """
        ticket_id = self.kwargs["ticket_id"]
        ticket = get_object_or_404(FeedbackTicket, ticket_id=ticket_id)

        # Check permissions explicitly for the parent ticket
        self.check_object_permissions(self.request, ticket)

        return TicketMessage.objects.filter(ticket=ticket)

    def perform_create(self, serializer):
        """
        When a message is posted, automatically attach the current user
        and the specific ticket ID.
        """
        ticket_id = self.kwargs["ticket_id"]
        ticket = get_object_or_404(FeedbackTicket, ticket_id=ticket_id)

        # Check permissions explicitly before saving
        self.check_object_permissions(self.request, ticket)

        # Logic: If user replies, maybe change status to 'Open'?
        # If admin replies, change status to 'In Progress'?
        if self.request.user.is_staff:
            ticket.status = "in_progress"
            ticket.save()

        serializer.save(sender=self.request.user, ticket=ticket)
