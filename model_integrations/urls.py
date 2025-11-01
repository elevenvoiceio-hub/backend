from django.urls import path

from model_integrations.labs import (
    LabsTaskDetailView,
    LabsTaskHistoryView,
    LabsTaskSubtitleView,
    LabsTextToSpeechAPIView,
    LabsVoicesAPIView,
)
from .views import (
    GcpTTSAPIView,
    AzureTextToSpeechAPIView,
    ElevenLabsTTSView,
    ModelLabsTextToSpeechAPIView,
    ModelLabsFetchAudioStatusAPIView,
    SpeechifyTTSAPIView,
    LemonFoxTTSAPIView,
)

urlpatterns = [
    path("gcp/", GcpTTSAPIView.as_view(), name="gcp-tts"),
    path("azure/", AzureTextToSpeechAPIView.as_view(), name="azure-tts"),
    path("elevenlabs/", ElevenLabsTTSView.as_view(), name="elevenlabs-tts"),
    path("model_labs/", ModelLabsTextToSpeechAPIView.as_view(), name="text-to-speech"),
    path(
        "model_labs/fetch-audio/<str:audio_id>/",
        ModelLabsFetchAudioStatusAPIView.as_view(),
        name="fetch-audio-status",
    ),
    path("speechify/", SpeechifyTTSAPIView.as_view(), name="speechify-tts"),
    path("lemonfox/", LemonFoxTTSAPIView.as_view(), name="lemonfox-tts"),
    # Labs API endpoints
    path("labs/voices/", LabsVoicesAPIView.as_view(), name="labs-voices"),
    path("labs/tts/", LabsTextToSpeechAPIView.as_view(), name="labs-text-to-speech"),
    path("labs/task", LabsTaskHistoryView.as_view(), name="labs-task-history"),
    path(
        "labs/task/<str:task_id>",
        LabsTaskDetailView.as_view(),
        name="labs-task-detail",
    ),
    path(
        "labs/task/subtitle/<str:task_id>",
        LabsTaskSubtitleView.as_view(),
        name="labs-task-subtitle",
    ),
]
