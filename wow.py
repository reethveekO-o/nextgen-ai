from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import os
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load system prompt
with open("onesec.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

def chat_with_pipo(message, history):
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, ai_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": ai_msg})
    messages.append({"role": "user", "content": message})
    
    # Generate response
    response = ollama.chat(model="pipo", messages=messages)

    json_response = {
        "role": "assistant",
        "content": response["message"]["content"]
    }
    
    # Save AI response
    with open("chat_log.txt", "w", encoding="utf-8") as f:
        f.write(response["message"]["content"])
    
    return json_response

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message")
        history = data.get("history", [])

        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        response = chat_with_pipo(message, history)
        return jsonify(response)  # Ensure JSON output

    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        return jsonify({"message": "File uploaded successfully", "file_path": file_path})

    except Exception as e:
        return jsonify({"error": "File upload failed", "details": str(e)}), 500

API_KEY = "a8c4570729dd47808c6b09fc492f77ec"
USER_ID = "FxkJVoFB6Ga8XoQBMg4DhMpKoZ43"

@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.json
        text = data.get("text")
        if not text:
            return jsonify({"error": "Text is required for speech synthesis"}), 400
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "X-User-ID": USER_ID,
            "Content-Type": "application/json"
        }

        payload = {
            "voice": "s3://voice-cloning-zero-shot/62fecf8c-34c2-4067-aea2-aca7ec6d7033/donald-trump/manifest.json",
            "text": text,
            "voice_engine": "PlayHT2.0"
        }

        response = requests.post("https://api.play.ht/api/v2/tts", json=payload, headers=headers)

        if response.status_code == 200:
            audio_url = response.json().get("audio_url")
            return jsonify({"audio_url": audio_url})
        else:
            return jsonify({"error": "Failed to generate speech", "details": response.json()}), response.status_code

    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
