import os
from tqdm import tqdm
import requests
from voice_generation import get_audio_from_text

def find_keys(target_key, dictionary, results=None):
    if results is None:
        results = []
    for key, value in dictionary.items():
        if key == target_key:
            results.append(value)
        elif isinstance(value, dict):
            find_keys(target_key, value, results)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    find_keys(target_key, item, results)
    return results

def slide_to_image(slides_service, presentation_id, slide_id, filename):
    response = slides_service.presentations().pages().getThumbnail(presentationId=presentation_id, pageObjectId=slide_id).execute()
    url = response["contentUrl"]
    image_data = requests.get(url).content
    with open(filename, "wb") as handler:
        handler.write(image_data)



def get_speaker_notes(slides_service, presentation_id, slide_id):
    slide = slides_service.presentations().pages().get(presentationId=presentation_id, pageObjectId=slide_id).execute()
    notes = slide.get("slideProperties").get("notesPage")
    content = find_keys("content", notes)
    return "\n".join(content)
    

def extract_slide_images(slides_service, presentation_id, output_dir):
    '''
    Creates PNG files that correspond to the slides of the presentation
    and saves them under the output_dir
    '''
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_ids = [(slide["objectId"], i) for i, slide in enumerate(slides)]
    for slide_id, i in tqdm(slide_ids):
        img_filename = os.path.join(output_dir, f"slide_{i}.png")
        slide_to_image(slides_service, presentation_id, slide_id, img_filename)

def extract_speaker_notes_to_mp3(slides_service, presentation_id, output_dir, voice="default"):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_ids = [(slide["objectId"], i) for i, slide in enumerate(slides)]
    for slide_id, i in tqdm(slide_ids):
        speaker_notes = get_speaker_notes(slides_service, presentation_id, slide_id)
        if speaker_notes.strip():
            filename = os.path.join(output_dir, f"slide_{i}.mp3")
            if not os.path.exists(filename):
                get_audio_from_text(voice, speaker_notes, filename)
