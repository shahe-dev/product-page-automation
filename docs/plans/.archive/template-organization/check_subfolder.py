"""Check Aggregator templates subfolder"""
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDENTIALS_PATH = Path(__file__).parent.parent / ".credentials" / "service-account-key.json"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_credentials():
    return service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH), scopes=SCOPES
    )

def main():
    creds = get_credentials()
    drive = build('drive', 'v3', credentials=creds)

    # The subfolder ID from the inventory
    folder_id = None

    # Find the Aggregator templates folder
    query = "name = 'Aggregator templates' and mimeType = 'application/vnd.google-apps.folder'"
    results = drive.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])

    if folders:
        folder_id = folders[0]['id']
        print(f"Found: Aggregator templates (ID: {folder_id})")

        # List contents
        file_query = f"'{folder_id}' in parents"
        file_results = drive.files().list(
            q=file_query,
            pageSize=100,
            fields="files(id, name, mimeType)"
        ).execute()

        files = file_results.get('files', [])
        print(f"\nContents ({len(files)} items):")
        for f in files:
            mime = f.get('mimeType', '')
            ftype = 'SHEET' if 'spreadsheet' in mime else 'FOLDER' if 'folder' in mime else 'FILE'
            print(f"  [{ftype}] {f['name']} - {f['id']}")
    else:
        print("Aggregator templates folder not found")

if __name__ == "__main__":
    main()
