import json
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from model_config_app.models import Configuration
from model_integrations.helper.helper import (
    check_user_subscription,
    increase_model_credits,
    reduce_character_credits,
)
from model_integrations.helper.labs_helper import get_labs_voices


class LabsVoicesAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get all voices available in Labs TTS service",
        responses={
            200: openapi.Response(
                description="List of all available voices",
                examples={
                    "application/json": {
                        "voices": [
                            {
                                "voice_id": "string",
                                "name": "string",
                                "language": "string",
                                "language_code": "string",
                                "gender": "string",
                                "preview_url": "string",
                                "styles": ["string"],
                                "high_quality": "boolean",
                            }
                        ]
                    }
                },
            ),
            400: "Bad Request - No active configuration found",
            401: "Unauthorized - Invalid API key",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(active=True, provider="labs")
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(get_labs_voices(api_key))


class LabsTextToSpeechAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Create an asynchronous text-to-speech task using Labs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["input", "voice_id", "model_id"],
            properties={
                "input": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Text to convert to speech"
                ),
                "voice_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="ID of the voice to use"
                ),
                "model_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="TTS model ID",
                    enum=[
                        "eleven_multilingual_v2",
                        "eleven_turbo_v2_5",
                        "eleven_flash_v2_5",
                        "eleven_v3",
                    ],
                ),
                "style": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Style (0.0 - 1.0)",
                    default=0.0,
                ),
                "speed": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Speed of speech (0.7 - 1.2)",
                    default=1.0,
                ),
                "use_speaker_boost": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Whether to use speaker boost",
                    default=False,
                ),
                "similarity": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Voice similarity (0.0 - 1.0)",
                    default=0.75,
                ),
                "stability": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Voice stability (0.0 - 1.0)",
                    default=0.5,
                ),
                "call_back_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Callback URL for completion notification",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Task successfully created",
                examples={"application/json": {"task_id": "task-uuid-12345"}},
            ),
            400: "Bad Request - Invalid parameters or no active configuration",
            401: "Unauthorized - Invalid API key",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(
                active=True, provider="labs", is_tts=True
            )
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs TTS configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Required fields
        required_fields = ["input", "voice_id", "model_id"]
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {"error": f"Missing required field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not check_user_subscription(request.user):
            return Response(
                {"error": "User does not have an active subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not reduce_character_credits(
            request.user, len(request.data.get("input", ""))
        ):
            return Response(
                {"error": "User does not have enough character credits."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import math

        multiplier = getattr(config, "token_multiplier", 1.0) or 1.0
        try:
            multiplier = float(multiplier)
        except Exception:
            multiplier = 1.0
        if multiplier <= 1.0:
            multiplier = 1.0
        credits = math.ceil(len(request.data.get("input", "")) * multiplier)
        increase_model_credits(credits, config)
        # Build the payload
        payload = {
            "input": request.data["input"],
            "voice_id": request.data["voice_id"],
            "model_id": request.data["model_id"],
            "speed": request.data["speed"] if request.data.get("speed", None) else 1,
        }

        # Add optional fields if they are present in the request
        optional_fields = [
            "style",
            "use_speaker_boost",
            "similarity",
            "stability",
            "call_back_url",
        ]
        for field in optional_fields:
            if field in request.data:
                payload[field] = request.data[field]

        # --- Validate optional field ranges ---

        # Validate speed (0.7 - 1.2)
        speed = payload.get("speed")
        if speed is not None and not (0.7 <= speed <= 1.2):
            return Response(
                {"error": "Speed must be between 0.7 and 1.2"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate style (0.0 - 1.0)
        style = payload.get("style")
        if style is not None and not (0.0 <= style <= 1.0):
            return Response(
                {"error": "Style must be between 0.0 and 1.0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate similarity (0.0 - 1.0)
        similarity = payload.get("similarity")
        if similarity is not None and not (0.0 <= similarity <= 1.0):
            return Response(
                {"error": "Similarity must be between 0.0 and 1.0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate stability (0.0 - 1.0)
        stability = payload.get("stability")
        if stability is not None and not (0.0 <= stability <= 1.0):
            return Response(
                {"error": "Stability must be between 0.0 and 1.0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- API Call ---

        # Update URL to the correct task endpoint
        url = "https://genaipro.vn/api/v1/labs/task"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            # Return the task ID
            return Response(response.json(), status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            # Check if the exception has a response attribute (i.e., it's an HTTPError)
            if hasattr(e, "response") and e.response is not None:
                error_status = e.response.status_code
                if e.response.status_code == 401:
                    error_message = "Invalid API key"
                elif e.response.status_code == 429:
                    error_message = "Too many requests"
                elif e.response.status_code == 400:
                    error_message = f"Bad Request: {e.response.text}"
                else:
                    try:
                        # Try to get error from API response
                        error_message = e.response.json().get("detail", error_message)
                    except requests.exceptions.JSONDecodeError:
                        error_message = e.response.text  # Fallback to raw text

            return Response(
                {"error": error_message},
                status=error_status,
            )


class LabsTaskHistoryView(APIView):
    """
    API view to retrieve the user's task history from Labs.
    """

    @swagger_auto_schema(
        operation_description="Get user's task history with pagination",
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Number of tasks per page",
                type=openapi.TYPE_INTEGER,
                default=20,
            ),
        ],
        responses={
            200: openapi.Response(
                description="A paginated list of tasks",
                examples={
                    "application/json": {
                        "tasks": [
                            {
                                "id": "000-000-000-000",
                                "input": "Hello world",
                                "voice_id": "uju3wxzG5OhpWcoi3SMy",
                                "model_id": "eleven_multilingual_v2",
                                "status": "completed",
                                "result": "https://...mp3",
                                "subtitle": "https://...srt",
                            }
                        ],
                        "total": 1,
                        "page": "1",
                        "limit": "20",
                    }
                },
            ),
            401: "Unauthorized - Invalid API key",
            500: "Internal Server Error",
        },
    )
    def get(self, request):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(
                active=True, provider="labs", is_tts=True
            )
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs TTS configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Base URL for the task endpoint
        url = "https://genaipro.vn/api/v1/labs/task"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Get query parameters for pagination
        params = {
            "page": request.query_params.get("page", 1),
            "limit": request.query_params.get("limit", 20),
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raises HTTPError for bad responses
            return Response(response.json(), status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            if hasattr(e, "response") and e.response is not None:
                error_status = e.response.status_code
                if e.response.status_code == 401:
                    error_message = "Invalid API key"
                else:
                    try:
                        error_message = e.response.json().get("detail", error_message)
                    except requests.exceptions.JSONDecodeError:
                        error_message = e.response.text

            return Response({"error": error_message}, status=error_status)


class LabsTaskDetailView(APIView):
    """
    API view to get or delete a specific Labs TTS task.
    """

    @swagger_auto_schema(
        operation_description="Get task details by task_id",
        responses={
            200: openapi.Response(
                description="Task details",
                examples={
                    "application/json": {
                        "id": "000-000-000-000",
                        "input": "Hello world",
                        "voice_id": "uju3wxzG5OhpWcoi3SMy",
                        "model_id": "eleven_multilingual_v2",
                        "style": 0.5,
                        "speed": 1,
                        "status": "completed",
                        "result": "https://...mp3",
                        "subtitle": "https://...srt",
                    }
                },
            ),
            401: "Unauthorized - Invalid API key",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def get(self, request, task_id):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(
                active=True, provider="labs", is_tts=True
            )
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs TTS configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # URL for the specific task
        url = f"https://genaipro.vn/api/v1/labs/task/{task_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            if hasattr(e, "response") and e.response is not None:
                error_status = e.response.status_code
                if e.response.status_code == 401:
                    error_message = "Invalid API key"
                elif e.response.status_code == 404:
                    error_message = "Task not found"
                else:
                    try:
                        error_message = e.response.json().get("detail", error_message)
                    except requests.exceptions.JSONDecodeError:
                        error_message = e.response.text

            return Response({"error": error_message}, status=error_status)

    @swagger_auto_schema(
        operation_description="Delete task by task_id",
        responses={
            200: openapi.Response(description="Task successfully deleted"),
            401: "Unauthorized - Invalid API key",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def delete(self, request, task_id):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(
                active=True, provider="labs", is_tts=True
            )
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs TTS configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # URL for the specific task
        url = f"https://genaipro.vn/api/v1/labs/task/{task_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            # Doc says 200 OK, return empty body or a success message
            return Response(status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            if hasattr(e, "response") and e.response is not None:
                error_status = e.response.status_code
                if e.response.status_code == 401:
                    error_message = "Invalid API key"
                elif e.response.status_code == 404:
                    error_message = "Task not found"
                else:
                    try:
                        error_message = e.response.json().get("detail", error_message)
                    except requests.exceptions.JSONDecodeError:
                        error_message = e.response.text

            return Response({"error": error_message}, status=error_status)


class LabsTaskSubtitleView(APIView):
    """
    API view to export a subtitle for a specific Labs TTS task.
    """

    @swagger_auto_schema(
        operation_description="Export subtitle for a task",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "max_characters_per_line": openapi.Schema(
                    type=openapi.TYPE_INTEGER, default=40
                ),
                "max_lines_per_cue": openapi.Schema(
                    type=openapi.TYPE_INTEGER, default=2
                ),
                "max_seconds_per_cue": openapi.Schema(
                    type=openapi.TYPE_INTEGER, default=5
                ),
            },
            description="Optional formatting parameters for the subtitle",
        ),
        responses={
            200: openapi.Response(description="Subtitle export successfully requested"),
            401: "Unauthorized - Invalid API key",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def post(self, request, task_id):
        # Get active Labs configuration
        try:
            config = Configuration.objects.get(
                active=True, provider="labs", is_tts=True
            )
            api_key = config.api_key
        except Configuration.DoesNotExist:
            return Response(
                {"error": "No active Labs TTS configuration found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = f"https://genaipro.vn/api/v1/labs/task/subtitle/{task_id}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Pass the request data as the JSON payload
        payload = request.data

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            # Doc says 200 OK, return empty body or a success message
            return Response(status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            if hasattr(e, "response") and e.response is not None:
                error_status = e.response.status_code
                if e.response.status_code == 401:
                    error_message = "Invalid API key"
                elif e.response.status_code == 404:
                    error_message = "Task not found"
                else:
                    try:
                        error_message = e.response.json().get("detail", error_message)
                    except requests.exceptions.JSONDecodeError:
                        error_message = e.response.text

            return Response({"error": error_message}, status=error_status)
