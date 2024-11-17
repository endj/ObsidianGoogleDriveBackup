# Backup and Upload Script

Automates:
1. Zipping a specified folder (e.g., Obsidian notes).
2. Uploading the zipped file to a designated Google Drive folder.

## Configuration

### Config file

```json
{
    "folder_to_zip": "/path/to/your/folder",
    "backup_folder_id": "<your_google_drive_folder_id>"
}
```

### Scopes
- **`https://www.googleapis.com/auth/drive.file`**: Grants file management access.

### Secrets

Stored and gitignored in secrets folder

1. **`credentials.json`**: OAuth2 credentials from the Google Cloud Console.
2. **`token.json`**: Stores tokens for subsequent script runs (created after first authentication).

## Usage

### Prerequisites

Requires Google cloud project and more:
https://developers.google.com/drive/api/quickstart/python

Install dependencies:
```sh
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```
```sh
python3 backup.py config.json
```
