from django.urls import path
from .views import (
    VoiceCloneCreateAPIView,
    VoiceClonesDeleteAPIView,
    VoiceClonesListAPIView,
)

urlpatterns = [
    path(
        "create/",
        VoiceCloneCreateAPIView.as_view(),
        name="voice-clone-create",
    ),
    path("clones/", VoiceClonesListAPIView.as_view(), name="voiceClones-list"),
    path(
        "clones/delete/<str:clone_id>/",
        VoiceClonesDeleteAPIView.as_view(),
        name="voiceclone-delete-custom",
    ),
]
