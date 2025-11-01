from django.urls import path
from .views import (
    VoiceCloneCreateAPIView,
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
        VoiceClonesListAPIView.as_view(),
        name="voiceclone-delete-custom",
    ),
]
