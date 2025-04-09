import os
import time
import requests
from pydub import AudioSegment
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import simpleaudio as sa  # Alternative playback module

last_modified_time = 0  # Track last file modification time
processing_flag = False  # Flag to prevent duplicate execution

# API Credentials (Use Environment Variables for Security)
API_KEY = "9bcaacf878a84cbfb7f6888645216893"
USER_ID = "2144un0tQaNg0eOEVO8L7tKJk212"

TEXT_FILE = "chat_log.txt"
OUTPUT_DIR = "audio_outputs"

# PlayHT API Endpoint
URL = "https://api.play.ht/api/v2/tts/stream"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "X-User-ID": USER_ID,
    "Content-Type": "application/json",
    "Accept": "audio/mpeg"
}

def generate_speech():
    """Reads text from file, sends to PlayHT API, saves, and plays the output audio."""
    global processing_flag

    if processing_flag:
        print("⚠ Speech generation already in progress. Skipping duplicate call.")
        return

    processing_flag = True  # Set flag to prevent duplicates
    time.sleep(0.2)  # Allow time for file write completion

    try:
        with open(TEXT_FILE, "r", encoding="utf-8") as file:
            text = file.read().strip()

        if not text:
            print("⚠ Text file is empty. Skipping TTS.")
            processing_flag = False
            return

        # Generate unique filenames using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_file = os.path.join(OUTPUT_DIR, f"output_{timestamp}.mp3")
        wav_file = os.path.join(OUTPUT_DIR, f"output_{timestamp}.wav")

        # Payload for PlayHT API
        data = {
            "voice": "s3://voice-cloning-zero-shot/8c031ab6-cb60-4dd9-8d93-bd4e0e8be1b1/rithvik/manifest.json",
            "text": text,
            "voice_engine": "PlayHT2.0"
        }

        # Send request to PlayHT API
        response = requests.post(URL, headers=HEADERS, json=data, stream=True)

        if response.status_code == 200:
            with open(mp3_file, "wb") as audio_file:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        audio_file.write(chunk)
            print(f"✅ Audio saved as MP3: {mp3_file}")

            # Convert MP3 to WAV
            audio = AudioSegment.from_file(mp3_file, format="mp3")
            audio.export(wav_file, format="wav")
            print(f"🔄 Converted to WAV: {wav_file}")

            # Release file handle before playing
            del audio  
            time.sleep(0.5)  # Allow OS time to release the file

            # 🎵 Play the WAV audio using simpleaudio (prevents double playback)
            wave_obj = sa.WaveObject.from_wave_file(wav_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()  # Ensure only one playback
            print(f"▶ Playing: {wav_file}")

        else:
            print(f"❌ Error: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"⚠ Error occurred: {e}")

    processing_flag = False  # Reset flag after processing


class FileChangeHandler(FileSystemEventHandler):
    """Detects changes to the text file and triggers TTS processing with debounce."""
    def on_modified(self, event):
        global last_modified_time

        if event.src_path.endswith(TEXT_FILE):
            current_time = time.time()

            # Ignore rapid successive events (debouncing)
            if current_time - last_modified_time < 2:  # 2-second debounce
                return

            last_modified_time = current_time
            print("\n🔄 File updated! Generating new speech output...")
            generate_speech()


if __name__ == "__main__":
    print(f"👀 Watching '{TEXT_FILE}' for changes...")

    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()