from django.urls import path
from .views import (
    PaymentConfigListCreateAPIView,
    PaymentConfigDetailAPIView,
    PaymentConfigGetOneAPIView,
)

urlpatterns = [
    path(
        "configs/",
        PaymentConfigListCreateAPIView.as_view(),
        name="paymentconfig-list-create",
    ),
    path(
        "configs/<int:pk>/",
        PaymentConfigDetailAPIView.as_view(),
        name="paymentconfig-detail",
    ),
    path(
        "default/", PaymentConfigGetOneAPIView.as_view(), name="paymentconfig-get-one"
    ),
]
