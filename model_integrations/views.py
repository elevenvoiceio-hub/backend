# views.py
import json
import base64
import io

import requests
from openai import OpenAI
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from model_config_app.models import Configuration
from model_integrations.helper.helper import increase_model_credits
from model_integrations.helper.speechify_helper import speechify_tts
from model_integrations.helper.lemonfox_helper import lemonfox_tts
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from model_integrations.helper.azure_helper import azure_tts
from model_integrations.helper.eleven_labs_helper_api import elevenlabs_tts
from model_integrations.helper.gcp_helper import gcp_tts
from model_integrations.serializers import (
    GcpTTSRequestSerializer,
    AzureTTSRequestSerializer,
)


class AzureTextToSpeechAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Optional: remove if open access

    def post(self, request):
        # Validate input data with serializer
        serializer = AzureTTSRequestSerializer(data=request.data)
        user = request.user
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        validated_data = serializer.validated_data
        text = validated_data["text"]
        voice_name = validated_data["voice_name"]
        audio_format = validated_data.get("audio_format", "MP3")
        azure_region = validated_data.get("azure_region", None)
        azure_subscription_key = validated_data.get("azure_subscription_key", None)
        if not azure_region or not azure_subscription_key:
            return Response(
                {"error": "Azure region and subscription key are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not text or not voice_name:
            return Response(
                {"error": "Both 'text' and 'voice_name' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Call the azure_tts function to generate speech
            success, result = azure_tts(
                text=text,
                voice_name=voice_name,
                audio_format=audio_format,
                user=user,
                azure_region=azure_region,
                azure_subscription_key=azure_subscription_key,
            )

            if success:
                # Prepare the response data
                response_data = {
                    "message": "Audio generated successfully.",
                    "filename": result["filename"],
                    "audio_base64": result["audio_base64"],
                    "format": result["format"],
                }

                return Response(response_data, status=status.HTTP_200_OK)

            else:
                return Response(
                    {"error": result}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GcpTTSAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print(user)
        print(f"User: {user.username} - Request Data: {request.data}")
        serializer = GcpTTSRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        validated_data = serializer.validated_data
        text = validated_data["text"]
        language_code = validated_data["language_code"]
        voice_name = validated_data["voice_name"]
        audio_format = validated_data.get("audio_format", "MP3")
        speaking_rate = validated_data.get("speaking_rate", 1.0)
        pitch = validated_data.get("pitch", 0.0)
        credentials_path = validated_data.get("credentials_path", None)
        if not text or not language_code or not voice_name:
            return Response(
                {
                    "error": "Both 'text', 'language_code', and 'voice_name' are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # Call the gcp_tts function to generate speech
            result = gcp_tts(
                user=user,
                text=text,
                language_code=language_code,
                voice_name=voice_name,
                audio_format=audio_format,
                speaking_rate=speaking_rate,
                pitch=pitch,
                credentials_path=credentials_path,
            )

            # Prepare the response data
            response_data = {
                "message": "Audio generated successfully.",
                "filename": result["filename"],
                "audio_base64": result["audio_base64"],
                "format": result["format"],
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ElevenLabsTTSView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            text = request.data.get("text", "")
            voice_id = request.data.get("voice_id", "")
            output_format = request.data.get("output_format", "mp3_44100_128")
            model_id = request.data.get("model_id", "eleven_multilingual_v2")
            user = request.user
            config = Configuration.objects.filter(
                provider="elevenlabs", active=True, is_tts=True
            )
            if not config.exists():
                return Response(
                    {"error": "ElevenLabs TTS configuration not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            increase_model_credits(len(text), config.first())
            api_key = config.first().api_key
            if not api_key:
                return Response(
                    {"error": "API key for ElevenLabs TTS is not configured."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not text or not voice_id:
                return Response(
                    {"detail": "Missing 'text' or 'voice_id'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            filename, base64_audio = elevenlabs_tts(
                user=user,
                api_key=api_key,
                text=text,
                voice_id=voice_id,
                output_format=output_format,
                model_id=model_id,
            )
            if filename and base64_audio:
                return Response(
                    {"filename": filename, "base64": base64_audio},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "TTS conversion failed. Check logs for error details."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ModelLabsTextToSpeechAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract request data
        key = request.data.get("key")
        prompt = request.data.get("prompt")
        language = request.data.get("language", "american english")
        voice_id = request.data.get("voice_id")
        speed = request.data.get("speed", 1)
        emotion = request.data.get("emotion", False)

        # Validate required fields
        if not all([key, prompt, voice_id]):
            return Response(
                {
                    "error": "Missing required fields: 'key', 'prompt', and 'voice_id' are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = "https://modelslab.com/api/v6/voice/text_to_speech"

        payload = json.dumps(
            {
                "key": key,
                "prompt": prompt,
                "language": language,
                "voice_id": voice_id,
                "speed": speed,
                "emotion": emotion,
            }
        )

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "error": "Failed to connect to the text-to-speech service.",
                    "details": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class ModelLabsFetchAudioStatusAPIView(APIView):
    def post(self, request, audio_id):
        key = request.data.get("key")

        if not key:
            return Response(
                {"error": "Missing required field: 'key' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = f"https://modelslab.com/api/v6/voice/fetch/{audio_id}"

        payload = json.dumps({"key": key})

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "error": "Failed to connect to the fetch audio service.",
                    "details": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class LemonFoxTTSAPIView(APIView):
    """
    LemonFox Text-to-Speech API endpoints for voice synthesis and voice listing.

    This API provides endpoints to:
    - Generate speech from text using LemonFox's TTS service
    - List available voices from LemonFox
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Generate speech from text using LemonFox TTS.

        Converts the provided text to speech using the specified voice and returns the audio as base64.

        Request Body:
            application/json:
                schema:
                    type: object
                    required:
                        - text
                        - voice
                    properties:
                        text:
                            type: string
                            description: The text to convert to speech
                            example: "Hello, this is a test of text to speech."
                        voice:
                            type: string
                            description: The voice ID to use for synthesis
                            example: "sarah"
                        model:
                            type: string
                            description: The TTS model to use
                            default: "tts-1"
                            example: "tts-1"
                        response_format:
                            type: string
                            description: The audio format to return
                            default: "mp3"
                            enum: ["mp3", "wav", "opus"]
                            example: "mp3"

        Responses:
            200:
                description: Successfully generated audio
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                message:
                                    type: string
                                    description: Success message
                                audio_base64:
                                    type: string
                                    description: Base64 encoded audio data
                                format:
                                    type: string
                                    description: Audio format (mp3, wav, etc)
            400:
                description: Missing required fields or invalid request
            404:
                description: LemonFox configuration not found
            502:
                description: Error generating audio

        Security:
            - Bearer Authentication: []
        """
        text = request.data.get("text")
        voice = request.data.get("voice")  # Changed from voice_id to voice
        response_format = request.data.get(
            "response_format", "mp3"
        )  # Added response_format parameter
        model = request.data.get("model", "tts-1")  # Added model parameter
        user = request.user

        if not text or not voice:
            return Response(
                {"error": "Both 'text' and 'voice' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = Configuration.objects.filter(
            provider="lemonfox", active=True, is_tts=True
        ).first()
        if not config:
            return Response(
                {"error": "LemonFox TTS configuration not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        increase_model_credits(len(text), config)
        api_key = config.api_key
        if not api_key:
            return Response(
                {"error": "API key for LemonFox TTS is not configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            audio_base64, format = lemonfox_tts(
                text=text,
                voice=voice,
                model=model,
                response_format=response_format,
                api_key=api_key,
                user=user,
            )

            response_data = {
                "message": "Audio generated successfully.",
                "audio_base64": audio_base64,
                "format": format,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"LemonFox TTS failed: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class SpeechifyTTSAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text")
        voice_id = request.data.get("voice_id")
        output_format = request.data.get("output_format", "mp3")
        user = request.user
        if not text or not voice_id:
            return Response(
                {"error": "Both 'text' and 'voice_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        config = Configuration.objects.filter(
            provider="speechify", active=True, is_tts=True
        ).first()
        if not config:
            return Response(
                {"error": "Speechify TTS configuration not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        increase_model_credits(len(text), config)
        token = config.api_key
        if not token:
            return Response(
                {"error": "API key for Speechify TTS is not configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            audio_base64, format = speechify_tts(
                text=text,
                voice_id=voice_id,
                output_format=output_format,
                token=token,
                user=user,
            )
            response_data = {
                "message": "Audio generated successfully.",
                "audio_base64": audio_base64,
                "format": format,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Speechify TTS failed: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
