from django.urls import path
from .views import ConfigurationView, ToggleModelActivationView, ActiveConfigurationsView, VoicesByModel

urlpatterns = [
    path('configurations/', ConfigurationView.as_view(), name='configurations'),
    path('configurations/toggle/', ToggleModelActivationView.as_view(), name='toggle-configurations'),
    path('configurations/active/', ActiveConfigurationsView.as_view(), name='active-configurations'),
    path('<int:model_id>/voices/', VoicesByModel.as_view(), name='voices-by-model')
]
