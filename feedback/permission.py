from rest_framework import permissions


class IsTicketOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of the ticket or admins
    to view and chat.
    """

    def has_object_permission(self, request, view, obj):
        # If the object is a TicketMessage, check permissions on the related ticket
        if hasattr(obj, "ticket"):
            return obj.ticket.created_by == request.user or request.user.role in [
                "admin",
                "subadmin",
            ]

        # If the object is the Ticket itself
        return obj.created_by == request.user or request.user.role in [
            "admin",
            "subadmin",
        ]
