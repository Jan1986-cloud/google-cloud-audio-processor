# Gebruik een officiële Python runtime als basisimage
FROM python:3.11-slim

# Installeer het ffmpeg programma
RUN apt-get update && apt-get install -y ffmpeg

# Stel de werkdirectory in de container in
WORKDIR /app

# Kopieer de dependencies file en installeer ze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY . .

# Start het Functions Framework. De --signature-type=event is de sleutel!
# Dit vertelt de container om te luisteren naar events, niet naar HTTP-requests.
CMD exec functions-framework --target=process_audio_gcs --signature-type=event
