from django.contrib import admin
from .models import FeedbackTicket


@admin.register(FeedbackTicket)
class FeedbackTicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_id",
        "created_by",
        "status",
        "category",
        "subject",
        "priority",
        "created_on",
    )
    list_filter = ("status", "category", "priority")
    search_fields = ("subject", "created_by__username")
