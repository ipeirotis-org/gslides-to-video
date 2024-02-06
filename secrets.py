from google.cloud import secretmanager
from google.oauth2 import service_account

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'gslides-to-video.json'
PROJECT_ID = "gslides-to-video"
VERSION_ID = "latest" 

# Load the credentials from the service account file
CREDENTIALS = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/cloud-platform'])



# Example usage

secret_id = "elevenlabs_api_key"
 # Can be "latest" or a specific version number

def access_secret_version(secret_id):

    # Initialize the Secret Manager client with the credentials
    client = secretmanager.SecretManagerServiceClient(credentials=CREDENTIALS)

    # Construct the resource name of the secret version
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{VERSION_ID}"
    
    # Access the secret version
    response = client.access_secret_version(request={"name": name})
    
    return response.payload.data.decode("UTF-8")


def get_secrets():

    return {
        "elevenlabs_api_key": access_secret_version("elevenlabs_api_key")
        "auphonic_password": access_secret_version("auphonic_password")
        "auphonic_username": access_secret_version("auphonic_username")
    }

