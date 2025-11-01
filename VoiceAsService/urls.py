"""
URL configuration for VoiceAsService project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, re_path
from django.urls import path
from django.contrib.auth.decorators import login_required
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.views.generic import RedirectView

from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

schema_view = get_schema_view(
    openapi.Info(
        title="Voice As A Service Api",
        default_version="v1",
        description="API Documentation for Voice As Service. \n\n"
        "To authenticate: \n"
        "1. Use /api/user/login/ to get your token \n"
        "2. Click 'Authorize' button at the top \n"
        "3. In the popup, enter: Bearer <your_token> \n"
        "4. Click 'Authorize' to save",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
        security=[{"Bearer": []}],
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[JWTAuthentication],
    url="https://backend-0nbu.onrender.com" if not settings.DEBUG else None,
)


urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path("admin/", admin.site.urls),
    path("api/user/", include("user_app.urls")),
    path("api/subscriptions/", include("subscriptions_app.urls")),
    path("api/model/", include("model_config_app.urls")),
    path("api/voices/", include("model_voices_app.urls")),
    path("api/tts/", include("model_integrations.urls")),
    path("api/stt/", include("speech_to_text.urls")),
    path("api/email/", include("email_config.urls")),
    path("api/payment/", include("payment_config.urls")),
    path("api/feedback/", include("feedback.urls")),
    path("api/voice_cloning/", include("voice_cloning.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
