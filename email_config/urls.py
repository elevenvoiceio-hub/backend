from django.urls import path
from .views import (
    EmailConfigListCreateAPIView,
    EmailConfigDetailAPIView,
    GetDefaultEmailConfigAPIView,
)

urlpatterns = [
    path(
        "configs/",
        EmailConfigListCreateAPIView.as_view(),
        name="emailconfig-list-create",
    ),
    path(
        "configs/<int:pk>/",
        EmailConfigDetailAPIView.as_view(),
        name="emailconfig-detail",
    ),
    path(
        "default/",
        GetDefaultEmailConfigAPIView.as_view(),
        name="emailconfig-get-default",
    ),
]
