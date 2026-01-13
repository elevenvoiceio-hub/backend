from django.db import models
from django.conf import settings


class FeedbackTicket(models.Model):
    CATEGORY_CHOICES = [
        ("billing_inquiry", "Billing Inquiry"),
        ("feedback", "Feedback"),
        ("technical_inquiry", "Technical Inquiry"),
        ("general_inquiry", "General Inquiry"),
        ("improvement_idea", "Improvement Idea"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    ]
    ticket_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=255)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        FeedbackTicket, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: Boolean to easily style messages in UI (Agent vs User)
    is_internal_note = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender} on Ticket #{self.ticket.ticket_id}"
