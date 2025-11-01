from django.urls import path
from .views import (
    FeedbackTicketListCreateView,
    FeedbackTicketDetailView,
    UserTicketsView,
)

urlpatterns = [
    path("", FeedbackTicketListCreateView.as_view(), name="feedback-list-create"),
    path("<int:pk>/", FeedbackTicketDetailView.as_view(), name="feedback-detail"),
    path("my-tickets/", UserTicketsView.as_view(), name="user-tickets"),
]
