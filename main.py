import sys
import os
from tqdm import tqdm
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import storage, firestore

from voice_generation import get_audio_from_text
from video import create_video
from gslides import extract_slide_images, extract_speaker_notes_to_mp3

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


def process_presentation(slides_service, presentation_id, output_dir):
    # Extract images from slides
    extract_slide_images(slides_service, presentation_id, output_dir)

    # Optionally specify a voice for MP3 extraction
    voice = "panos"
    extract_speaker_notes_to_mp3(slides_service, presentation_id, output_dir, voice)



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
    process_presentation(slides_service, presentation_id, output_folder)

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
