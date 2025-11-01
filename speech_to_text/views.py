from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from model_config_app.models import Configuration
from .helper import speech_to_text, lemonfox_stt


class LemonFoxSpeechToTextAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        operation_summary="Convert Speech to Text using LemonFox",
        operation_description="Converts audio file to text using LemonFox's speech recognition",
        manual_parameters=[
            openapi.Parameter(
                "audio_file",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Audio file to transcribe",
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful transcription",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                        "provider": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request - Missing audio file or API key not configured",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        audio_file = request.FILES.get("audio_file", None)

        if not audio_file:
            return Response(
                {"error": "'audio_file' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model_config = Configuration.objects.filter(
            provider="lemonfox", is_stt=True, active=True
        ).first()

        if not model_config or not model_config.api_key:
            return Response(
                {"error": "LemonFox API key not configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Pass the file object directly to the helper
            text = lemonfox_stt(api_key=model_config.api_key, audio_file=audio_file)
            return Response(
                {"text": text, "provider": "lemonfox"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AutoSpeechToTextAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        operation_summary="Auto Speech to Text Conversion",
        operation_description="Automatically selects between OpenAI and LemonFox for speech to text conversion based on configured API keys. Prefers OpenAI when both are available.",
        manual_parameters=[
            openapi.Parameter(
                "audio_file",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Audio file to transcribe",
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful transcription",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                        "provider": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request - Missing audio file or no available API keys",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        audio_file = request.FILES.get("audio_file", None)

        if not audio_file:
            return Response(
                {"error": "'audio_file' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for OpenAI configuration
        openai_config = Configuration.objects.filter(
            provider="openai", is_stt=True, active=True
        ).first()

        # Check for LemonFox configuration
        lemonfox_config = Configuration.objects.filter(
            provider="lemonfox", is_stt=True, active=True
        ).first()

        # If neither configuration is available
        if not openai_config and not lemonfox_config:
            return Response(
                {"error": "No available speech to text configuration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Prefer OpenAI if available
            if openai_config and openai_config.api_key:
                text = speech_to_text(
                    api_key=openai_config.api_key, audio_file=audio_file
                )
                return Response(
                    {"text": text, "provider": "openai"}, status=status.HTTP_200_OK
                )
            # Fall back to LemonFox
            elif lemonfox_config and lemonfox_config.api_key:
                text = lemonfox_stt(
                    api_key=lemonfox_config.api_key, audio_file=audio_file
                )
                return Response(
                    {"text": text, "provider": "lemonfox"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "error": "No valid API keys configured for speech to text services."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OpenAISpeechToTextAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        operation_summary="Convert Speech to Text using OpenAI",
        operation_description="Converts audio file to text using OpenAI's speech recognition",
        manual_parameters=[
            openapi.Parameter(
                "audio_file",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Audio file to transcribe",
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful transcription",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                        "provider": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request - Missing audio file or API key",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        api_key = request.data.get("api_key", None)
        audio_file = request.FILES.get("audio_file", None)

        if not audio_file:
            return Response(
                {"error": "'audio_file' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not api_key:
            model_config = Configuration.objects.filter(
                provider="openai", is_stt=True, active=True
            ).first()
            api_key = model_config.api_key if model_config else None
        try:
            # Pass the file object directly to the helper
            text = speech_to_text(api_key=api_key, audio_file=audio_file)
            return Response(
                {"text": text, "provider": "openai"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
