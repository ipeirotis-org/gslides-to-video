from google.oauth2 import service_account
from googleapiclient.discovery import build


# @title Extract Images and Text from Google Slides


def slide_to_image(presentation_id, slide_id, filename):
    # Request image
    response = service.presentations().pages().getThumbnail(presentationId=presentation_id, pageObjectId=slide_id).execute()
    url = response["contentUrl"]

    # Download and save image
    image_data = requests.get(url).content
    with open(f"{filename}", "wb") as handler:
        handler.write(image_data)


def find_keys(target_key, dictionary, results=None):
    if results is None:
        results = []
    for key, value in dictionary.items():
        if key == target_key:
            results.append(value)
        if isinstance(value, dict):
            find_keys(target_key, value, results)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    find_keys(target_key, item, results)
    return results


def get_speaker_notes(presentation_id, slide_id):
    # Make API call to get slides information
    slide = service.presentations().pages().get(presentationId=presentation_id, pageObjectId=slide_id).execute()

    notes = slide.get("slideProperties").get("notesPage")
    content = find_keys("content", notes)

    text = "\n".join(content)

    return text


def extract_slides_and_text(presentation_id, output_dir):
    # Get presentation and slides
    presentation = service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_ids = list(enumerate([slide["objectId"] for slide in slides]))

    for i, slide_id in tqdm(slide_ids):
        img_filename = f"{output_dir}/slide_{i}.png"
        slide_to_image(presentation_id, slide_id, img_filename)

        speaker_notes = get_speaker_notes(presentation_id, slide_id)
        # print(speaker_notes)

        if speaker_notes.strip():  # Only proceed if there's text in the notes
            # Get audio using ElevenLabs API
            filename = f"{output_dir}/slide_{i}.mp3"
            if not os.path.exists(filename):
                get_audio_from_text(speaker_notes, filename)


def get_slide_service():
    # Path to your service account key file
    SERVICE_ACCOUNT_FILE = "gslides-to-video.json"

    # Define the scopes
    SCOPES = ["https://www.googleapis.com/auth/presentations.readonly"]

    # Authenticate and build the service
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build("slides", "v1", credentials=credentials)

    return service


def get_presentation(presentation_id):
    service = get_slide_service()

    # Get presentation details
    presentation = service.presentations().get(presentationId=presentation_id).execute()

    return presentation  # Or handle the presentation object as needed
