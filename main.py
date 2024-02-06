import sys
import os
from tqdm import tqdm
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import storage, firestore

from voice_generation import get_audio_from_text
from video import create_video

# Define constants for service accounts and scopes
SERVICE_ACCOUNT_FILE = "gslides-to-video.json"
SCOPES = [
    "https://www.googleapis.com/auth/presentations.readonly",
    "https://www.googleapis.com/auth/drive",
]


def initialize_google_services():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    slides_service = build("slides", "v1", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)
    firestore_client = firestore.Client(credentials=credentials)
    return slides_service, storage_client, firestore_client


def slide_to_image(slides_service, presentation_id, slide_id, filename):
    response = (
        slides_service.presentations().pages().getThumbnail(presentationId=presentation_id, pageObjectId=slide_id).execute()
    )
    url = response["contentUrl"]
    image_data = requests.get(url).content
    with open(filename, "wb") as handler:
        handler.write(image_data)


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


def get_speaker_notes(slides_service, presentation_id, slide_id):
    slide = slides_service.presentations().pages().get(presentationId=presentation_id, pageObjectId=slide_id).execute()
    notes = slide.get("slideProperties").get("notesPage")
    content = find_keys("content", notes)
    return "\n".join(content)


def extract_slides_and_text(slides_service, presentation_id, output_dir):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation["slides"]
    slide_ids = [(slide["objectId"], i) for i, slide in enumerate(slides)]
    for slide_id, i in tqdm(slide_ids):
        img_filename = os.path.join(output_dir, f"slide_{i}.png")
        slide_to_image(slides_service, presentation_id, slide_id, img_filename)
        speaker_notes = get_speaker_notes(slides_service, presentation_id, slide_id)
        if speaker_notes.strip():
            filename = os.path.join(output_dir, f"slide_{i}.mp3")
            if not os.path.exists(filename):
                # Assuming get_audio_from_text() is defined elsewhere
                voice = "panos"
                get_audio_from_text(voice, speaker_notes, filename)


def upload_to_bucket(storage_client, blob_name, file_path, bucket_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    return blob.public_url


def add_firestore_entry(firestore_client, presentation_id, metadata):
    doc_ref = firestore_client.collection("presentations").document(presentation_id)
    doc_ref.set(metadata)


def main(presentation_id):
    slides_service, storage_client, firestore_client = initialize_google_services()
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    title = presentation.get("title")
    output_folder = f"./content/slides/output/{title}/{presentation_id}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    extract_slides_and_text(slides_service, presentation_id, output_folder)
    # Assuming create_video is defined to accept slides_service as a parameter
    output_file = "output_video.mp4"
    create_video(slides_service, presentation_id, output_folder, output_file)
    video_path = os.path.join(output_folder, output_file)
    bucket_name = "gslide_videos"
    video_url = upload_to_bucket(storage_client, f"{title}/{presentation_id}/{output_file}", video_path, bucket_name)
    metadata = {
        "title": title,
        "presentation_id": presentation_id,
        "video_url": video_url,
    }
    add_firestore_entry(firestore_client, presentation_id, metadata)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <presentation_id>")
        sys.exit(1)
    presentation_id = sys.argv[1]
    main(presentation_id)
