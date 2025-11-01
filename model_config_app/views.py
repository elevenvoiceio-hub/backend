# views.py
import json
import os
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from model_integrations.helper.azure_helper import azure_populate_voices_table
from model_integrations.helper.eleven_labs_helper_api import (
    populate_elevenlabs_voices_table,
)
from model_integrations.helper.gcp_helper import populate_voice_model_from_gcp
from model_integrations.helper.labs_helper import populate_labs_voices_table
from model_integrations.helper.lemonfox_helper import populate_lemonfox_voices_table
from model_integrations.helper.modellabs_helper import populate_modellabs_voices_table
from model_integrations.helper.speechify_helper import populate_voices_table
from model_voices_app.models import Voice
from model_voices_app.serializer import VoiceSerializer
from permissions import IsAdmin
from .models import Configuration
from .serializers import ConfigurationSerializer, ToggleModelActivationSerializer

User = get_user_model()


def is_admin(user):
    return getattr(user, "role", "") == "Admin"


def is_sub_admin(user):
    return getattr(user, "role", "") == "Sub-admin"


def populate_voices_by_provider(provider, api_key=None):
    provider = provider.lower()
    if provider == "gcp":
        populate_voice_model_from_gcp(model_name=provider)
    elif provider == "speechify" and api_key:
        populate_voices_table(api_key)
    elif provider == "elevenlabs" and api_key:
        populate_elevenlabs_voices_table(api_key)
    elif provider == "azure":
        azure_populate_voices_table()
    elif provider == "modellabs" and api_key:
        populate_modellabs_voices_table(api_key)
    elif provider == "lemonfox" and api_key:
        populate_lemonfox_voices_table(api_key)
    elif provider == "labs" and api_key:
        populate_labs_voices_table(api_key)


class ConfigurationView(APIView):
    def get(self, request):
        configs = Configuration.objects.all()
        serializer = ConfigurationSerializer(configs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ConfigurationSerializer)
    def post(self, request):
        config = None
        try:
            gcp_config = request.data.get("gcp_config", None)
            api_key = request.data.get("api_key", None)
            is_clone = request.data.get("is_clone", False)
            is_stt = request.data.get("is_stt", False)
            is_tts = request.data.get("is_tts", False)
            serializer = ConfigurationSerializer(data=request.data)

            if serializer.is_valid():
                config = serializer.save()
                provider = serializer.validated_data.get(
                    "provider"
                ) or serializer.validated_data.get("model_name")

                # Handle GCP config JSON
                if provider and provider.lower() == "gcp" and gcp_config:
                    # Save the JSON to a file in the root directory
                    config_path = os.path.join(os.getcwd(), "gcp_config.json")
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(gcp_config, f)
                    # Update the api_key field to the file path
                    config.api_key = config_path
                    config.save()
                    api_key = config_path

                else:
                    api_key = serializer.validated_data.get("api_key") or getattr(
                        config, "api_key", None
                    )

                if provider:
                    populate_voices_by_provider(provider, api_key)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if config:
                config.delete()
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(request_body=ConfigurationSerializer)
    def put(self, request):
        gcp_config = request.data.get("gcp_config")
        try:
            config = Configuration.objects.get(id=request.data.get("id"))
        except Configuration.DoesNotExist:
            return Response(
                {"error": "Configuration not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ConfigurationSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            config = serializer.save()
            provider = serializer.validated_data.get(
                "provider"
            ) or serializer.validated_data.get("model_name")

            # Handle GCP config JSON
            if provider and provider.lower() == "gcp" and gcp_config:
                config_path = os.path.join(os.getcwd(), "gcp_config.json")
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(gcp_config, f)
                config.api_key = config_path
                config.save()
                api_key = config_path
            else:
                api_key = serializer.validated_data.get("api_key") or getattr(
                    config, "api_key", None
                )

            if provider:
                populate_voices_by_provider(provider, api_key)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            config = Configuration.objects.get(id=request.data.get("id"))
            config.delete()
            return Response(
                {"message": "Configuration deleted."}, status=status.HTTP_204_NO_CONTENT
            )
        except Configuration.DoesNotExist:
            return Response(
                {"error": "Configuration not found."}, status=status.HTTP_404_NOT_FOUND
            )


class ToggleModelActivationView(APIView):
    @swagger_auto_schema(request_body=ToggleModelActivationSerializer)
    def post(self, request):
        serializer = ToggleModelActivationSerializer(data=request.data)
        if serializer.is_valid():
            ids = serializer.validated_data["ids"]
            activate = serializer.validated_data["activate"]
            updated = Configuration.objects.filter(id__in=ids).update(active=activate)
            voices = Voice.objects.filter(model_id__in=ids)
            voices.update(is_active=activate)
            return Response({"message": f"{updated} configurations updated."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActiveConfigurationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_configs = Configuration.objects.filter(active=True)
        serializer = ConfigurationSerializer(active_configs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VoicesByModel(APIView):
    def get(self, request, model_id):
        voices = Voice.objects.filter(configuration_id=model_id)
        serialized = VoiceSerializer(voices, many=True)
        return Response({"voices": serialized.data}, status=status.HTTP_200_OK)
