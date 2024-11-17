import os
import zipfile
import json
import sys
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# If scope changes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SECRETS_FOLDER = "secrets"


def load_config(config_path):
    assert os.path.exists(config_path), f"Config file '{config_path}' does not exist."
    with open(config_path, "r") as file:
        config = json.load(file)
    assert "folder_to_zip" in config, "'folder_to_zip' is missing in the config."
    assert "backup_folder_id" in config, "'backup_folder_id' is missing in the config."
    return config


def zip_folder(folder_path, output_filename):
    assert os.path.exists(folder_path), f"Folder path '{folder_path}' does not exist."
    assert os.path.isdir(folder_path), f"Path '{folder_path}' is not a directory."

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zipf.write(file_path, arcname)
    assert os.path.exists(output_filename), f"Failed to create zip file '{output_filename}'."
    print(f"Folder zipped as {output_filename}")


def upload_file(file_path, file_name, backup_folder_id):
    assert os.path.exists(file_path), f"File path '{file_path}' does not exist."

    creds = None
    token_path = os.path.join(SECRETS_FOLDER, "token.json")
    credentials_path = os.path.join(SECRETS_FOLDER, "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            assert os.path.exists(credentials_path), "Missing 'credentials.json' for authentication."
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        os.makedirs(SECRETS_FOLDER, exist_ok=True)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)
        file_metadata = {
            "name": file_name,
            "parents": [backup_folder_id],
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        assert file.get('id'), "File upload failed. No file ID returned."
        print(f"File '{file_name}' uploaded successfully with ID: {file.get('id')}")

    except HttpError as error:
        print(f"An error occurred during file upload: {error}")
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 backup_to_drive.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = load_config(config_path)
        folder_to_zip = config["folder_to_zip"]
        backup_folder_id = config["backup_folder_id"]

        current_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_file_name = f"obsidian_{current_timestamp}.zip"

        zip_folder(folder_to_zip, zip_file_name)
        upload_file(zip_file_name, zip_file_name, backup_folder_id)

        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)
            print(f"Temporary file {zip_file_name} removed.")
    except AssertionError as error:
        print(f"AssertionError: {error}")
    except Exception as error:
        print(f"An unexpected error occurred: {error}")
