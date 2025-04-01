# Google Drive MCP Server

This project provides a Google Drive integration server using Claude MCP (Model Control Protocol) capabilities. It allows you to interact with Google Drive and Google Sheets directly through Claude.

## Setup Instructions

### 1. Google Cloud Project Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API and Google Sheets API
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the credentials and save as `credentials.json` in the project root

### 2. Environment Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running the Server

```bash
python gdrive_mcp_server.py
```

The first time you run the server, it will open a browser window for OAuth authentication. After authenticating, the credentials will be saved in `token.json`.

## Available Endpoints

### 1. Google Drive Search
- **Endpoint**: `/gdrive_search`
- **Method**: POST
- **Input**:
  ```json
  {
    "query": "search query",
    "pageToken": "optional_page_token",
    "pageSize": 10
  }
  ```

### 2. Google Drive File Read
- **Endpoint**: `/gdrive_read_file`
- **Method**: POST
- **Input**:
  ```json
  {
    "fileId": "google_drive_file_id"
  }
  ```

### 3. Google Sheets Read
- **Endpoint**: `/gsheets_read`
- **Method**: POST
- **Input**:
  ```json
  {
    "spreadsheetId": "spreadsheet_id",
    "ranges": ["Sheet1!A1:B10"],
    "sheetId": null
  }
  ```

### 4. Google Sheets Update Cell
- **Endpoint**: `/gsheets_update_cell`
- **Method**: POST
- **Input**:
  ```json
  {
    "fileId": "spreadsheet_id",
    "range": "Sheet1!A1",
    "value": "New Value"
  }
  ```

## Example Usage

```python
import requests

# Search for files
response = requests.post("http://localhost:8000/gdrive_search", json={
    "query": "name contains 'report'",
    "pageSize": 10
})
print(response.json())

# Read file content
response = requests.post("http://localhost:8000/gdrive_read_file", json={
    "fileId": "your_file_id"
})
print(response.json())

# Read from Google Sheets
response = requests.post("http://localhost:8000/gsheets_read", json={
    "spreadsheetId": "your_spreadsheet_id",
    "ranges": ["Sheet1!A1:D10"]
})
print(response.json())

# Update cell in Google Sheets
response = requests.post("http://localhost:8000/gsheets_update_cell", json={
    "fileId": "your_spreadsheet_id",
    "range": "Sheet1!A1",
    "value": "Updated Value"
})
print(response.json())
```

## Error Handling

The server returns appropriate HTTP status codes and error messages:
- 200: Successful operation
- 400: Invalid request parameters
- 401: Authentication error
- 403: Permission denied
- 404: Resource not found
- 500: Internal server error

## Security Notes

1. Keep your `credentials.json` and `token.json` files secure and never commit them to version control
2. The server runs on localhost by default - implement appropriate security measures if deploying to production
3. Implement rate limiting and request validation as needed for your use case