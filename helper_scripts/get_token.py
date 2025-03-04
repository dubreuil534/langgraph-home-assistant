import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load environment variables from .env (if needed)
load_dotenv()

# Calculate the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define local paths to the token and credentials files (adjust as needed)
TOKEN_PATH = os.path.join(script_dir, '..', 'google_credentials', 'token.json')
CREDENTIALS_PATH = os.path.join(script_dir, '..', 'google_credentials', 'credentials.json')

# Define the required API scopes.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/spreadsheets',
]

def get_token():
    """
    Load OAuth credentials for accessing Google APIs.
    This function loads credentials from disk, refreshes them if expired,
    or initiates a new OAuth flow if necessary.
    """
    creds = None

    # Load credentials from the token file if it exists.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If credentials are invalid or not available, start a new OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use the credentials file from the local path.
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
        # Save the newly obtained credentials to disk.
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds

if __name__ == '__main__':
    credentials = get_token()
    print("Credentials loaded successfully.")