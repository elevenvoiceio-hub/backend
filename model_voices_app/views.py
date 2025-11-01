from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from permissions import IsAdmin
from .models import Voice
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .serializer import VoiceSerializer


class VoiceListCreateView(APIView):
    # permission_classes = [IsAdmin]

    def get(self, request):
        voices = Voice.objects.all()
        serializer = VoiceSerializer(voices, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = VoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoiceDetailView(APIView):
    # permission_classes = [IsAdmin]

    def get_object(self, pk):
        return get_object_or_404(Voice, pk=pk)

    def get(self, request, pk):
        voice = self.get_object(pk)
        serializer = VoiceSerializer(voice)
        return Response(serializer.data)

    def put(self, request, pk):
        voice = self.get_object(pk)
        serializer = VoiceSerializer(voice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        voice = self.get_object(pk)
        voice.delete()
        return Response(
            {"message": "Voice deleted."}, status=status.HTTP_204_NO_CONTENT
        )


class ActivateDeactivateVoices(APIView):
    # permission_classes = [IsAdmin]

    def post(self, request):
        voice_ids = request.data.get("voice_ids", [])
        action = request.data.get("action")  # "activate" or "deactivate"

        if not isinstance(voice_ids, list) or action not in ["activate", "deactivate"]:
            return Response(
                {"error": "Invalid input."}, status=status.HTTP_400_BAD_REQUEST
            )

        is_active = True if action == "activate" else False
        updated = Voice.objects.filter(id__in=voice_ids).update(is_active=is_active)

        return Response(
            {
                "message": f"{updated} voices {'activated' if is_active else 'deactivated'}."
            }
        )


class ActiveVoicesAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        voices = Voice.objects.filter(is_active=True)
        serializer = VoiceSerializer(voices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FilterVoicesAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        model_id = request.query_params.get("model")
        language = request.query_params.get("language")
        gender = request.query_params.get("gender")
        accent = request.query_params.get("accent")
        country = request.query_params.get("country")
        timber = request.query_params.get("timber")
        search = request.query_params.get("search")

        voices = Voice.objects.all()

        if model_id:
            voices = voices.filter(model_id=model_id)
        if language:
            voices = voices.filter(language=language)
        if gender:
            voices = voices.filter(gender=gender)
        if accent:
            voices = voices.filter(accent=accent)
        if search:
            voices = voices.filter(name__icontains=search)
        # Filter by country in styles list
        if country:
            voices = voices.filter(styles__contains=[country])
        # Filter by timber in styles list
        if timber:
            voices = voices.filter(styles__contains=[timber])

        # You can filter by multiple styles (country, timber, etc.) at once
        # If both country and timber are provided, both must be in styles
        styles_filters = []
        if country:
            styles_filters.append(country)
        if timber:
            styles_filters.append(timber)
        # Add more style-based filters if needed (e.g., accent, etc.)
        # For accent as style, uncomment below:
        # if accent:
        #     styles_filters.append(accent)
        if styles_filters:
            for style in styles_filters:
                voices = voices.filter(styles__contains=[style])

        serializer = VoiceSerializer(voices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LanguagesByVoice(APIView):
    def get(self, request, voice_id):
        try:
            voice = Voice.objects.get(voice_id=voice_id)
            language = voice.language
            return Response({"languages": [language]}, status=status.HTTP_200_OK)
        except Voice.DoesNotExist:
            return Response(
                {"error": "Voice not found."}, status=status.HTTP_404_NOT_FOUND
            )


class VoiceByLanguage(APIView):
    def get(self, request, language_code):
        voices = Voice.objects.filter(language_code=language_code)
        if not voices.exists():
            return Response(
                {"error": "No voices found for this language."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VoiceSerializer(voices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActivateDeactivateVoicesByLanguage(APIView):
    # permission_classes = [IsAdmin]

    def post(self, request):
        language = request.data.get("language")
        action = request.data.get("action")  # "activate" or "deactivate"

        if not language or action not in ["activate", "deactivate"]:
            return Response(
                {"error": "Invalid input."}, status=status.HTTP_400_BAD_REQUEST
            )

        is_active = True if action == "activate" else False
        updated = Voice.objects.filter(language=language).update(is_active=is_active)

        return Response(
            {
                "message": f"{updated} voices {'activated' if is_active else 'deactivated'} for language '{language}'."
            }
        )


class VoiceByVoiceIdAPIView(APIView):
    def get(self, request, voice_id):
        try:
            voice = Voice.objects.get(voice_id=voice_id)
            serializer = VoiceSerializer(voice)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Voice.DoesNotExist:
            return Response(
                {"error": "Voice not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
