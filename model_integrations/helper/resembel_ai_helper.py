
from resemble import Resemble
Resemble.api_key('MsAHyb3l0HPN4INMHyUJGQtt')



def resemble_ai_tts(text,voice_uuid):
    # Get your default Resemble project.
    project_uuid = Resemble.v2.projects.all(1, 10)['items'][0]['uuid']

    # Get your Voice uuid. In this example, we'll obtain the first.
    voice_uuid = Resemble.v2.voices.all(1, 10)['items'][0]['uuid']
    page = 1
    page_size = 10

    response = Resemble.v2.voices.all(page, page_size)
    voices = response['items']
    print(voices)
    print(len(voices))

    # Let's create a clip!
    body = 'This is a test'
    response = Resemble.v2.clips.create_sync(project_uuid,
                                             voice_uuid,
                                             body,
                                             title=None,
                                             sample_rate=None,
                                             output_format=None,
                                             precision=None,
                                             include_timestamps=None,
                                             is_archived=None,
                                             raw=None)

    print(response)