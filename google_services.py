from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import storage, firestore

# Path to your service account key file
SERVICE_ACCOUNT_FILE = "gslides-to-video.json"

# Define constants for service accounts and scopes
PROJECT_ID = "gslides-to-video"
VERSION_ID = "latest"


def initialize_google_services():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    slides_service = build("slides", "v1", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)
    firestore_client = firestore.Client(credentials=credentials)
    secrets_client = secretmanager.SecretManagerServiceClient(credentials=credentials)
    gdrive_service = build("drive", "v3", credentials=credentials)
    return slides_service, storage_client, firestore_client, secrets_client, gdrive_service


def access_secret_version(secrets_client, secret_id):
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{VERSION_ID}"
    response = secrets_client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")



def list_google_slides():
    _, _, _, _, service = initialize_google_services()
    results = service.files().list(q="mimeType='application/vnd.google-apps.presentation'").execute()
    items = results.get("files", [])

    if not items:
        print("No Google Slides presentations found.")
        return []
    else:
        print("Google Slides presentations:")
        for item in items:
            print("{0}\t{1}".format(item["name"], item["id"]))
        return [(item["name"], item["id"]) for item in items]