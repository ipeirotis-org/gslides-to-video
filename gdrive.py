from google.oauth2 import service_account
from googleapiclient.discovery import build


def get_drive_service():
    SERVICE_ACCOUNT_FILE = "gslides-to-video.json"
    SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials)
    return service


def list_google_slides():
    service = get_drive_service()
    results = service.files().list(q="mimeType='application/vnd.google-apps.presentation'").execute()
    items = results.get("files", [])

    if not items:
        print("No Google Slides presentations found.")
    else:
        print("Google Slides presentations:")
        for item in items:
            print("{0}\t{1}".format(item["name"], item["id"]))


list_google_slides()
