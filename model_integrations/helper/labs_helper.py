import requests

from model_voices_app.models import Voice
from model_config_app.models import Configuration


def get_labs_voices(
    api_key: str,
    page: int = 0,
    page_size: int = 30,
    search: str = None,
    sort: str = None,
    language: str = None,
    accent: str = None,
    use_cases: list = None,
    category: str = None,
    gender: str = None,
    age: str = None,
    min_notice_period_days: int = None,
    include_custom_rates: bool = False,
    include_live_moderated: bool = True,
) -> dict:
    """
    Fetch available voices from Labs TTS API with filtering and pagination.

    Args:
        api_key (str): Labs API key
        page (int, optional): Page number. Defaults to 0.
        page_size (int, optional): Number of voices per page. Defaults to 30.
        search (str, optional): Search by voice name.
        sort (str, optional): Sort by (trending, created_date, cloned_by_count, usage_character_count_1y).
        language (str, optional): Filter by language.
        accent (str, optional): Filter by accent (american, british, australian, etc.).
        use_cases (list, optional): Filter by use cases (can select multiple).
        category (str, optional): Filter by category (premade, cloned, professional, etc.).
        gender (str, optional): Filter by gender (male, female, neutral).
        age (str, optional): Filter by age (young, middle_aged, old).
        min_notice_period_days (int, optional): Minimum notice period in days.
        include_custom_rates (bool, optional): Include custom rates. Defaults to False.
        include_live_moderated (bool, optional): Include live moderated voices. Defaults to True.

    Returns:
        dict: Dictionary containing voices list, total count, page info
            {
                "voices": list of voice dictionaries,
                "total": total number of voices,
                "page": current page number,
                "page_size": number of voices per page
            }

    Raises:
        Exception: If the API request fails
    """
    try:
        url = "https://genaipro.vn/api/v1/labs/voices"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Build query parameters
        params = {
            "page": page,
            "page_size": page_size,
            "include_custom_rates": str(include_custom_rates).lower(),
            "include_live_moderated": str(include_live_moderated).lower(),
        }

        # Add optional parameters if provided
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        if language:
            params["language"] = language
        if accent:
            params["accent"] = accent
        if use_cases:
            params["use_cases"] = use_cases
        if category:
            params["category"] = category
        if gender:
            params["gender"] = gender
        if age:
            params["age"] = age
        if min_notice_period_days is not None:
            params["min_notice_period_days"] = min_notice_period_days

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Get response data - now it's a direct list
        voices_list = response.json()

        # Filter to only return English and Indian languages
        # Accept both language codes (eg. 'hi', 'en', 'ta') and locales (eg. 'hi-IN', 'en-IN')
        # Also accept language names (eg. 'Hindi', 'Tamil') if provided.
        indian_codes = {
            "hi",
            "bn",
            "ta",
            "te",
            "kn",
            "ml",
            "mr",
            "gu",
            "pa",
            "ur",
            "or",
            "as",
        }

        def is_indian_or_english(voice_obj: dict) -> bool:
            # Check explicit language code field
            lang = (voice_obj.get("language") or "").strip().lower()
            if lang:
                # language may be a code like 'hi' or a name like 'Hindi'
                if lang == "en" or lang.startswith("en-") or lang == "english":
                    return True
                if lang in indian_codes:
                    return True
                # language as full name
                name = lang
                for indian_name in [
                    "hindi",
                    "bengali",
                    "tamil",
                    "telugu",
                    "kannada",
                    "malayalam",
                    "marathi",
                    "gujarati",
                    "punjabi",
                    "urdu",
                    "oriya",
                    "odia",
                    "assamese",
                ]:
                    if indian_name in name:
                        return True

            # Check locale like 'hi-IN' or 'en-US'
            locale = (voice_obj.get("locale") or "").strip().lower()
            if locale:
                prefix = locale.split("-")[0]
                if prefix == "en" or prefix in indian_codes:
                    return True

            # Check verified languages entries if present
            for v in voice_obj.get("verified_languages", []) or []:
                vl = (v.get("language") or v.get("locale") or "").strip().lower()
                if not vl:
                    continue
                vl_prefix = vl.split("-")[0]
                if vl_prefix == "en" or vl_prefix in indian_codes:
                    return True

            return False

        voices_list = [v for v in voices_list if is_indian_or_english(v)]

        # Format the voices to match our Voice model structure
        formatted_voices = []
        for voice in voices_list:
            # Get the primary language from verified_languages if available
            verified_langs = voice.get("verified_languages", [])
            primary_lang = None
            if verified_langs:
                primary_lang = verified_langs[0]

            voice_info = {
                "voice_id": voice.get("voice_id", ""),
                "voicename": voice.get("name", ""),
                "language": voice.get("language", "en"),
                "language_code": (
                    voice.get("locale", "en-US").upper()
                    if voice.get("locale")
                    else f"{voice.get('language', 'en')}-US".upper()
                ),
                "gender": voice.get("gender", ""),
                "accent": voice.get("accent", ""),
                "age": voice.get("age", ""),
                "category": voice.get("category", ""),
                "description": voice.get("description", ""),
                "preview_url": voice.get("preview_url", ""),
                "use_case": voice.get("use_case", ""),
                "cloned_by_count": voice.get("cloned_by_count", 0),
                "notice_period": voice.get("notice_period", 0),
                "verified_languages": [
                    {
                        "language": lang.get("language"),
                        "model_id": lang.get("model_id"),
                        "accent": lang.get("accent"),
                        "locale": lang.get("locale"),
                        "preview_url": lang.get("preview_url"),
                    }
                    for lang in voice.get("verified_languages", [])
                ],
                "usage_stats": {
                    "character_count_1y": voice.get("usage_character_count_1y", 0),
                    "character_count_7d": voice.get("usage_character_count_7d", 0),
                    "play_api_usage_1y": voice.get(
                        "play_api_usage_character_count_1y", 0
                    ),
                },
            }
            formatted_voices.append(voice_info)

        # Calculate total from the list length since it's a direct list now
        total = len(formatted_voices)

        # Handle pagination in memory since API might not support it
        start_idx = page * page_size
        end_idx = start_idx + page_size
        paginated_voices = formatted_voices[start_idx:end_idx]

        # Return paginated response with formatted voices
        return {
            "voices": paginated_voices,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if hasattr(e.response, "status_code"):
            if e.response.status_code == 401:
                error_message = "Invalid or expired API key"
            elif e.response.status_code == 429:
                error_message = "Too many requests"
        raise Exception(f"Failed to fetch Labs voices: {error_message}")


def populate_labs_voices_table(api_key: str = None):
    """
    Fetch the list of supported voices from Labs and populate the Voice model.

    Args:
        api_key (str, optional): Labs API key. If not provided, will try to get from Configuration.

    Returns:
        None
    """
    config = Configuration.objects.filter(
        provider="labs", active=True, is_tts=True
    ).first()

    if not config:
        print("Error: Labs Config not found or inactive.")
        return

    if not api_key:
        if not config.api_key:
            print("Error: Labs API key not configured.")
            return
        api_key = config.api_key

    try:
        voices_response = get_labs_voices(api_key)
    except Exception as e:
        print(f"Error fetching voices from Labs: {e}")
        return
    voice_list = voices_response.get("voices", [])

    if not voice_list:
        print("No voices were returned from the Labs API.")
        return
    updated_count = 0
    created_count = 0

    for voice_data in voice_list:
        _, created = Voice.objects.update_or_create(
            voice_id=voice_data["voice_id"],
            defaults={
                "voicename": voice_data["voicename"],
                "language": voice_data["language"],
                "language_code": voice_data["language_code"],
                "gender": voice_data["gender"],
                "sample_url": voice_data["preview_url"],
                "is_active": True,
                "model": config,
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    print(
        f"Voice model populated from Labs voices. "
        f"Created: {created_count}, Updated: {updated_count}, Total: {len(voice_list)}"
    )
