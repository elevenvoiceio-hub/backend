from rest_framework import serializers

class GcpTTSRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    language_code = serializers.CharField(required=True)
    voice_name = serializers.CharField(required=True)
    audio_format = serializers.ChoiceField(choices=["MP3", "OGG_OPUS", "LINEAR16"], default="MP3")
    speaking_rate = serializers.FloatField(required=False, default=1.0)
    pitch = serializers.FloatField(required=False, default=0.0)
    credentials_path = serializers.CharField(required=False, allow_blank=True)

class AzureTTSRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    voice_name = serializers.CharField(required=True)
    audio_format = serializers.ChoiceField(choices=["MP3", "WAV", "OGG"], default="MP3")