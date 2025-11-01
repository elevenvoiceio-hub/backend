from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import FeedbackTicket


class FeedbackTicketTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.ticket = FeedbackTicket.objects.create(
            created_by=self.user,
            status="open",
            category="feedback",
            subject="Test Subject",
            priority="medium",
        )

    def test_ticket_creation(self):
        self.assertEqual(self.ticket.subject, "Test Subject")
        self.assertEqual(self.ticket.created_by, self.user)
