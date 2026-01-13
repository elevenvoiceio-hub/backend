from elevenlabs import ElevenLabs
from rest_framework import permissions, status
from rest_framework.response import Response
from model_config_app.models import Configuration
from .models import VoiceClones
from .serializers import VoiceClonesSerializer
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
import os
import tempfile
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from speechify import Speechify


class VoiceCloneWrapper:
    @staticmethod
    def get_active_voice_model():
        # Get all active clone models
        active_models = Configuration.objects.filter(active=True, is_clone=True)
        if not active_models:
            return None, "No active voice cloning models found."

        # Return the first active model
        return active_models.first(), None

    @staticmethod
    def create_voice_clone(request, model_data):
        if model_data.provider == "elevenlabs":
            return VoiceCloneWrapper._create_elevenlabs_voice(request, model_data)
        elif model_data.provider == "speechify":
            return VoiceCloneWrapper._create_speechify_voice(request, model_data)
        else:
            return None, f"Unsupported model: {model_data.provider}"

    @staticmethod
    def _create_elevenlabs_voice(request, model_data):
        name = request.data.get("name")
        description = request.data.get("description", "")
        files = request.FILES.getlist("sample")
        remove_background_noise = request.data.get("remove_background_noise", False)
        language = request.data.get("language", "en")
        gender = request.data.get("gender", "other")

        temp_file_paths = []
        try:
            # Save uploaded files temporarily
            temp_dir = tempfile.gettempdir()
            for f in files:
                path = os.path.join(temp_dir, f.name)
                with open(path, "wb+") as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                temp_file_paths.append(path)

            client = ElevenLabs(api_key=model_data.api_key)
            voice = client.voices.ivc.create(
                name=name,
                description=description,
                files=temp_file_paths,
                remove_background_noise=remove_background_noise,
            )

            user_voice = VoiceClones(
                user=request.user,
                voice_cloning_model=model_data,
                clone_name=name,
                clone_id=voice.id,
                gender=gender,
                language=language,
            )
            user_voice.save()

            voice_data = {
                "id": voice.id,
                "name": voice.name,
                "description": voice.description,
                "user_email": request.user.email,
                "provider": "elevenlabs",
            }
            return voice_data, None
        except Exception as e:
            return None, str(e)
        finally:
            # Clean up temp files
            for path in temp_file_paths:
                if os.path.exists(path):
                    os.remove(path)

    @staticmethod
    def _create_speechify_voice(request, model_data):
        # Required fields
        name = request.data.get("name")
        gender = request.data.get("gender")
        consent = request.data.get("consent")
        sample_file = request.FILES.get("sample")
        # Optional fields
        locale = request.data.get("locale", "en-US")
        avatar_file = request.FILES.get("avatar")

        # Validate required fields
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not gender:
            missing_fields.append("gender")
        if not consent:
            missing_fields.append("consent")
        if not sample_file:
            missing_fields.append("sample")
        if missing_fields:
            return None, f"Missing required fields: {', '.join(missing_fields)}"

        try:
            # Save sample and avatar files temporarily
            temp_sample_path = None
            temp_avatar_path = None
            sample_obj = None
            avatar_obj = None

            if sample_file:
                temp_dir = tempfile.gettempdir()
                temp_sample_path = os.path.join(temp_dir, sample_file.name)
                with open(temp_sample_path, "wb+") as destination:
                    for chunk in sample_file.chunks():
                        destination.write(chunk)
                sample_obj = open(temp_sample_path, "rb")

            if avatar_file:
                temp_dir = tempfile.gettempdir()
                temp_avatar_path = os.path.join(temp_dir, avatar_file.name)
                with open(temp_avatar_path, "wb+") as destination:
                    for chunk in avatar_file.chunks():
                        destination.write(chunk)
                avatar_obj = open(temp_avatar_path, "rb")

            client = Speechify(token=model_data.api_key)
            voice = client.tts.voices.create(
                name=name,
                gender=gender,
                locale=locale,
                sample=sample_obj,
                avatar=avatar_obj,
                consent=consent,
            )

            user_voice = VoiceClones(
                user=request.user,
                voice_cloning_model=model_data,
                clone_name=name,
                clone_id=voice.id,
                gender=gender,
                language=locale,
            )
            user_voice.save()

            voice_data = {
                "id": voice.id,
                "display_name": getattr(voice, "display_name", name),
                "gender": voice.gender,
                "locale": getattr(voice, "locale", locale),
                "type": getattr(voice, "type", "personal"),
                "avatar_image": getattr(voice, "avatar_image", None),
                "user_email": request.user.email,
                "provider": "speechify",
            }
            return voice_data, None
        except Exception as e:
            return None, str(e)
        finally:
            # Clean up temp files and close file objects
            if "sample_obj" in locals() and sample_obj:
                sample_obj.close()
            if "avatar_obj" in locals() and avatar_obj:
                avatar_obj.close()
            if temp_sample_path and os.path.exists(temp_sample_path):
                os.remove(temp_sample_path)
            if temp_avatar_path and os.path.exists(temp_avatar_path):
                os.remove(temp_avatar_path)


class VoiceCloneCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="""Create a new voice clone using the active voice cloning service.
        
For ElevenLabs:
- Required: name, sample (audio files)
- Optional: description, remove_background_noise, gender, language (default: 'en')

For Speechify:
- Required: name, gender, sample (single audio file), consent
- Optional: locale (default: 'en-US'), avatar
        """,
        manual_parameters=[
            openapi.Parameter(
                "name",
                openapi.IN_FORM,
                description="Voice name (required for both services)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "sample",
                openapi.IN_FORM,
                description="Audio file(s). For ElevenLabs: multiple files allowed. For Speechify: single file required.",
                type=openapi.TYPE_FILE,
                required=True,
                multiple=True,
            ),
            openapi.Parameter(
                "gender",
                openapi.IN_FORM,
                description="Gender. Required for Speechify (male/female/notSpecified), optional for ElevenLabs (default: other)",
                type=openapi.TYPE_STRING,
                enum=["male", "female", "notSpecified", "other"],
                required=False,
            ),
            openapi.Parameter(
                "description",
                openapi.IN_FORM,
                description="Voice description (ElevenLabs only)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "remove_background_noise",
                openapi.IN_FORM,
                description="Remove background noise (ElevenLabs only)",
                type=openapi.TYPE_BOOLEAN,
                default=False,
            ),
            openapi.Parameter(
                "language",
                openapi.IN_FORM,
                description="Language code. For ElevenLabs: 'en', for Speechify: 'en-US' format",
                type=openapi.TYPE_STRING,
                default="en",
            ),
            openapi.Parameter(
                "consent",
                openapi.IN_FORM,
                description='Consent JSON string (Required for Speechify only). Format: {"fullName": "John Doe", "email": "john@example.com"}',
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "avatar",
                openapi.IN_FORM,
                description="Avatar image file (Speechify only)",
                type=openapi.TYPE_FILE,
            ),
        ],
        responses={
            201: openapi.Response(
                "Voice created",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "voice": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "description": openapi.Schema(type=openapi.TYPE_STRING),
                                "display_name": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "gender": openapi.Schema(type=openapi.TYPE_STRING),
                                "locale": openapi.Schema(type=openapi.TYPE_STRING),
                                "type": openapi.Schema(type=openapi.TYPE_STRING),
                                "avatar_image": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "user_email": openapi.Schema(type=openapi.TYPE_STRING),
                                "provider": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    enum=["elevenlabs", "speechify"],
                                ),
                            },
                        )
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message",
                        )
                    },
                ),
            ),
            404: openapi.Response(
                "Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message when no active voice model is found",
                        )
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        # Get active voice model
        model_data, error = VoiceCloneWrapper.get_active_voice_model()
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create voice clone using the wrapper
        voice_data, error = VoiceCloneWrapper.create_voice_clone(request, model_data)
        if error:
            return Response(
                {"error": f"Failed to create voice clone: {error}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"voice": voice_data}, status=status.HTTP_201_CREATED)

    # ...existing code...


class VoiceClonesListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all voice clones for the authenticated user.",
        responses={200: VoiceClonesSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        user_voices = VoiceClones.objects.filter(user=request.user)
        serializer = VoiceClonesSerializer(user_voices, many=True)
        data = serializer.data
        # Add user_email and provider/model to each item
        for item, obj in zip(data, user_voices):
            item["user_email"] = request.user.email
            # Try to get provider/model name from related model
            provider = None
            if hasattr(obj, "voice_cloning_model") and obj.voice_cloning_model:
                provider = getattr(obj.voice_cloning_model, "provider", None)
            item["provider"] = provider
        return Response(data)


class VoiceClonesDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a voice clone by its clone_id for the authenticated user.",
        responses={200: VoiceClonesSerializer(), 404: "Not found"},
    )
    def get(self, request, clone_id, *args, **kwargs):
        """Return a single voice clone owned by the authenticated user."""
        obj = VoiceClones.objects.filter(user=request.user, clone_id=clone_id).first()
        if not obj:
            return Response(
                {"error": "Voice clone not found or you don't have permission."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = VoiceClonesSerializer(obj)
        data = serializer.data
        data["user_email"] = request.user.email
        provider = None
        if hasattr(obj, "voice_cloning_model") and obj.voice_cloning_model:
            provider = getattr(obj.voice_cloning_model, "provider", None)
            data["provider"] = provider
            data["model_name"] = getattr(obj.voice_cloning_model, "model_name", None)
        return Response(data)

    def delete(self, request, clone_id, *args, **kwargs):

        deleted_count, _ = VoiceClones.objects.filter(
            user=request.user, clone_id=clone_id
        ).delete()

        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # This handles both "not found" and "not owned by user"
            return Response(
                {"error": "Voice clone not found or you don't have permission."},
                status=status.HTTP_404_NOT_FOUND,
            )
