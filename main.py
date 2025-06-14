import base64
import os
import ffmpeg
from datetime import datetime
import json

from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATIE ---
PROJECT_ID = "gen-lang-client-0695866337"
LOCATION = "europe-west4"
SPREADSHEET_ID = "1WjrSSjGQb-RxxRnxL51ksW--6XT1nTegwUviog_SFLE"
# --- EINDE CONFIGURATIE ---

vertexai.init(project=PROJECT_ID, location=LOCATION)
storage_client = storage.Client()

def process_audio_gcs(event, context):
    try:
        file_data = event["data"]
        bucket_name = file_data["bucket"]
        file_name = file_data["name"]

        print(f"START: Verwerken van bestand '{file_name}'.")

        # 1. Download het bestand
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        input_bytes = blob.download_as_bytes()
        print(f"DOWNLOADED: {len(input_bytes)} bytes.")

        # 2. Converteer naar MP3
        print("CONVERTING: Start FFmpeg conversie...")
        ffmpeg_output, ffmpeg_error = ffmpeg.run(
            ffmpeg.input('pipe:0').output('pipe:1', format='mp3', acodec='libmp3lame', ab='192k'),
            input=input_bytes,
            capture_stdout=True,
            capture_stderr=True
        )
        if ffmpeg_error:
            print(f"FFMPEG INFO/ERROR: {ffmpeg_error.decode('utf8')}")
        print(f"CONVERTED: MP3-grootte: {len(ffmpeg_output)} bytes.")
        
        # 3. Roep Gemini aan
        print("CALLING GEMINI...")
        multimodal_model = GenerativeModel("gemini-1.5-flash-001")
        prompt = """
          Analyseer de bijgevoegde audio van een telefoongesprek. Voer de volgende taken uit en retourneer het resultaat uitsluitend als een JSON-object:
          1.  **Transcribeer** het gesprek volledig.
          2.  **Identificeer de sprekers** (bv. "Beller", "Medewerker" of specifieke namen indien genoemd).
          3.  Schrijf een beknopte **samenvatting** van het gesprek.
          4.  Wijs relevante **labels** toe uit deze lijst of maak nieuwe indien nodig: privé, verkoop, support, actie vereist, spoed, info.
          5.  Indien een vervolgactie nodig is, geef de **datum** waarop dit moet gebeuren in 'YYYY-MM-DD' formaat. Anders, geef "".
          6.  Benoem de concrete **actie** die nodig is (bv. "Offerte sturen", "Terugbellen"). Anders, geef "".

          JSON-structuur:
          { "speakers": "string", "transcription": "string", "summary": "string", "labels": ["string", "string"], "followUpDate": "YYYY-MM-DD" | "", "action": "string" | "" }
        """
        response = multimodal_model.generate_content([
            Part.from_data(data=ffmpeg_output, mime_type="audio/mpeg"), prompt
        ])
        result_text = response.text
        print("GEMINI RESPONSE RECEIVED.")
        
        # 4. Schrijf naar Google Sheets
        print("WRITING TO SHEETS...")
        data = json.loads(result_text)
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file_name,
            data.get("speakers", "Onbekend"), data.get("transcription", "Transcriptie mislukt"),
            data.get("summary", ""), ', '.join(data.get("labels", [])),
            data.get("followUpDate", ""), data.get("action", "")
        ]
        
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_authorized_user_info(info=None, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        body = {'values': [row_data]}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Transcripts!A1",
            valueInputOption="USER_ENTERED", body=body).execute()
        
        print(f"SUCCESS: Volledig verwerkt en weggeschreven naar sheet.")

    except Exception as e:
        print(f"FATAL ERROR during processing: {e}")
