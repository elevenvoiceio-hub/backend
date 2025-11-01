from django.urls import path
from .views import (
    VoiceByVoiceIdAPIView,
    VoiceListCreateView,
    VoiceDetailView,
    ActivateDeactivateVoices,
    ActiveVoicesAPIView,
    FilterVoicesAPIView,
    LanguagesByVoice,
    VoiceByLanguage,
    ActivateDeactivateVoicesByLanguage,
)

urlpatterns = [
    path("", VoiceListCreateView.as_view(), name="voice-list-create"),
    path("<int:pk>/", VoiceDetailView.as_view(), name="voice-detail"),
    path(
        "toggle/",
        ActivateDeactivateVoices.as_view(),
        name="activate-deactivate-voices",
    ),
    path("active/", ActiveVoicesAPIView.as_view(), name="active-voices"),
    path("filter/", FilterVoicesAPIView.as_view(), name="filter-voices"),
    path(
        "<str:voice_id>/languages/",
        LanguagesByVoice.as_view(),
        name="languages-by-voice",
    ),
    path(
        "language/<str:language_code>/",
        VoiceByLanguage.as_view(),
        name="voice-by-language",
    ),
    path(
        "toggle-language/",
        ActivateDeactivateVoicesByLanguage.as_view(),
        name="activate-deactivate-voices-by-language",
    ),
    path(
        "voice/<str:voice_id>/",
        VoiceByVoiceIdAPIView.as_view(),
        name="voice-by-voice-id",
    ),
]
