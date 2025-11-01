from django.urls import path
from .views import (
    OpenAISpeechToTextAPIView,
    LemonFoxSpeechToTextAPIView,
    AutoSpeechToTextAPIView,
)

urlpatterns = [
    path(
        "openai/",
        OpenAISpeechToTextAPIView.as_view(),
        name="openai-speech-to-text",
    ),
    path(
        "lemonfox/",
        LemonFoxSpeechToTextAPIView.as_view(),
        name="lemonfox-speech-to-text",
    ),
    path(
        "",
        AutoSpeechToTextAPIView.as_view(),
        name="auto-speech-to-text",
    ),
]
