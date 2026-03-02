"""
Centralized configuration for template organization scripts.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
CREDENTIALS_PATH = PROJECT_ROOT / ".credentials" / "service-account-key.json"

# Google API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.readonly',
]

# Shared Drive for automation outputs (no quota issues)
SHARED_DRIVE_ID = "0AOEEIstP54k2Uk9PVA"

# Legacy folder (personal Drive - read only recommended)
TEMPLATE_COLLECTION_FOLDER = "Template Collection"

# Output directories
SCRAPED_PAGES_DIR = BASE_DIR / "scraped_pages"
SCRAPED_PAGES_DIR.mkdir(exist_ok=True)


def get_credentials():
    """Load service account credentials."""
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES
    )


def get_drive_service():
    """Get authenticated Drive service."""
    from googleapiclient.discovery import build
    return build('drive', 'v3', credentials=get_credentials())


def get_sheets_service():
    """Get authenticated Sheets service."""
    from googleapiclient.discovery import build
    return build('sheets', 'v4', credentials=get_credentials())


def create_file_in_shared_drive(name, mime_type='application/vnd.google-apps.spreadsheet'):
    """Create a file in the Shared Drive."""
    drive = get_drive_service()

    file_metadata = {
        'name': name,
        'mimeType': mime_type,
        'parents': [SHARED_DRIVE_ID]
    }

    created_file = drive.files().create(
        body=file_metadata,
        supportsAllDrives=True
    ).execute()

    return created_file['id']
