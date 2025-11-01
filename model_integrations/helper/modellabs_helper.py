import requests
from model_voices_app.models import Voice
from model_config_app.models import Configuration


def populate_modellabs_voices_table(
    api_key="5kvIE5ImQdQCTIdHULWRpyRWZijEXtvyEJnheQz4r7ZrBZp890RYlnvhyrRS",
):
    """
    Fetch the list of supported voices from Model Labs (if endpoint exists) and populate the Voice model.
    """
    url = "https://modelslab.com/api/v6/voice"  # Hypothetical endpoint!
    headers = {"Content-Type": "application/json"}
    payload = {"key": api_key}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    voices = data.get("voices", [])

    config, _ = Configuration.objects.get_or_create(model_name="ModelLabs")

    for voice in voices:
        voicename = voice.get("name", "")
        voice_id = voice.get("voice_id", "")
        gender = voice.get("gender", "")
        sample_url = voice.get("sample_url", "")
        style_list = ",".join(voice.get("styles", [])) if voice.get("styles") else ""
        language_code = voice.get("language_code", "")
        language = voice.get("language", language_code)

        Voice.objects.update_or_create(
            voice_id=voice_id,
            defaults={
                "language": language,
                "language_code": language_code,
                "voicename": voicename,
                "gender": gender,
                "sample_url": sample_url,
                "style_list": style_list,
                "is_active": True,
                "model": config,
            },
        )

    print("Voice model populated from Model Labs voices.")
