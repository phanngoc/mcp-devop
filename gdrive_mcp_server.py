from typing import Optional, List
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

app = FastAPI()

def get_google_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

# Models for request validation
class SearchRequest(BaseModel):
    query: str
    pageToken: Optional[str] = None
    pageSize: Optional[int] = 10

class FileReadRequest(BaseModel):
    fileId: str

class SheetsReadRequest(BaseModel):
    spreadsheetId: str
    ranges: Optional[List[str]] = None
    sheetId: Optional[int] = None

class SheetsUpdateRequest(BaseModel):
    fileId: str
    range: str
    value: str

@app.post("/gdrive_search")
async def gdrive_search(request: SearchRequest):
    try:
        creds = get_google_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        query = service.files().list(
            q=request.query,
            pageSize=min(request.pageSize, 100),
            pageToken=request.pageToken,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        return {
            "files": query.get('files', []),
            "nextPageToken": query.get('nextPageToken')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gdrive_read_file")
async def gdrive_read_file(request: FileReadRequest):
    try:
        creds = get_google_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        # Get file metadata
        file = service.files().get(fileId=request.fileId).execute()
        
        # Download file content
        request = service.files().get_media(fileId=request.fileId)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        content = fh.getvalue().decode('utf-8')
        return {
            "filename": file['name'],
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gsheets_read")
async def gsheets_read(request: SheetsReadRequest):
    try:
        creds = get_google_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        if request.ranges:
            result = service.spreadsheets().values().batchGet(
                spreadsheetId=request.spreadsheetId,
                ranges=request.ranges
            ).execute()
            return {"valueRanges": result.get('valueRanges', [])}
        else:
            # Get the first sheet if no specific ranges provided
            result = service.spreadsheets().values().get(
                spreadsheetId=request.spreadsheetId,
                range='A1:ZZ'
            ).execute()
            return {"values": result.get('values', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gsheets_update_cell")
async def gsheets_update_cell(request: SheetsUpdateRequest):
    try:
        creds = get_google_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        body = {
            'values': [[request.value]]
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=request.fileId,
            range=request.range,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return {
            "updatedRange": result.get('updatedRange'),
            "updatedCells": result.get('updatedCells')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 