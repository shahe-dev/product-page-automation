"""
Inventory templates from Google Drive folder "template collection"
and analyze Google Sheets structure for consolidation planning.
"""

import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDENTIALS_PATH = Path(__file__).parent.parent / ".credentials" / "service-account-key.json"

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

def get_credentials():
    return service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES
    )

def list_drive_folder(folder_name="template collection"):
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    folder_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    folder_results = drive_service.files().list(
        q=folder_query,
        fields="files(id, name)"
    ).execute()

    folders = folder_results.get('files', [])
    if not folders:
        print(f"Folder '{folder_name}' not found. Listing all accessible files...")
        all_files = drive_service.files().list(
            pageSize=100,
            fields="files(id, name, mimeType, parents)"
        ).execute()
        return all_files.get('files', [])

    folder_id = folders[0]['id']
    print(f"Found folder: {folders[0]['name']} (ID: {folder_id})")

    file_query = f"'{folder_id}' in parents"
    file_results = drive_service.files().list(
        q=file_query,
        pageSize=100,
        fields="files(id, name, mimeType, webViewLink)"
    ).execute()

    return file_results.get('files', [])

def read_sheet_structure(sheet_id):
    creds = get_credentials()
    sheets_service = build('sheets', 'v4', credentials=creds)

    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id,
            includeGridData=False
        ).execute()

        sheet_info = {
            'title': spreadsheet.get('properties', {}).get('title', 'Unknown'),
            'spreadsheet_id': sheet_id,
            'sheets': []
        }

        for sheet in spreadsheet.get('sheets', []):
            props = sheet.get('properties', {})
            sheet_name = props.get('title', 'Unknown')

            range_name = f"'{sheet_name}'!A1:Z100"
            try:
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=range_name
                ).execute()
                values = result.get('values', [])

                sheet_data = {
                    'name': sheet_name,
                    'row_count': len(values),
                    'headers': values[0] if values else [],
                    'all_data': values
                }
            except Exception as e:
                sheet_data = {
                    'name': sheet_name,
                    'error': str(e)
                }

            sheet_info['sheets'].append(sheet_data)

        return sheet_info

    except Exception as e:
        return {'error': str(e), 'spreadsheet_id': sheet_id}

def main():
    print("=" * 60)
    print("TEMPLATE COLLECTION INVENTORY")
    print("=" * 60)

    files = list_drive_folder("template collection")

    print(f"\nFound {len(files)} files:\n")

    spreadsheets = []
    other_files = []

    for f in files:
        mime = f.get('mimeType', '')
        if 'spreadsheet' in mime:
            spreadsheets.append(f)
            print(f"  [SHEET] {f['name']}")
            print(f"          ID: {f['id']}")
        else:
            other_files.append(f)
            print(f"  [OTHER] {f['name']} ({mime})")

    print(f"\n{'=' * 60}")
    print(f"SPREADSHEETS: {len(spreadsheets)} | OTHER: {len(other_files)}")
    print("=" * 60)

    if spreadsheets:
        print("\nANALYZING SPREADSHEET STRUCTURES...\n")

        all_structures = {}

        for sheet in spreadsheets:
            print(f"Reading: {sheet['name']}...")
            structure = read_sheet_structure(sheet['id'])
            all_structures[sheet['name']] = structure

            if 'error' not in structure:
                print(f"  Tabs: {len(structure['sheets'])}")
                for tab in structure['sheets']:
                    if 'error' not in tab:
                        print(f"    - {tab['name']}: {tab['row_count']} rows")
                    else:
                        print(f"    - {tab['name']}: ERROR - {tab['error']}")
            else:
                print(f"  ERROR: {structure['error']}")

        output_path = Path(__file__).parent / "template_inventory.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_structures, f, indent=2, ensure_ascii=False)

        print(f"\nFull analysis saved to: {output_path}")

if __name__ == "__main__":
    main()
