from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from langdetect import detect
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import uuid
import tempfile

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Initialize Translator & Recognizer
recognizer = sr.Recognizer()
translator = Translator()

# Temp directory for generated audio files
TEMP_DIR = tempfile.gettempdir()

# Language mapping
LANGUAGE_MAP = {
    'zh-cn': 'zh-CN', 'zh-tw': 'zh-TW', 'en': 'en', 'es': 'es',
    'fr': 'fr', 'de': 'de', 'ja': 'ja', 'ru': 'ru', 'hi': 'hi'
}

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    """Receive real-time audio and convert it to text."""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    language = request.form.get('language', 'en')

    try:
        # Save the temporary audio file
        filename = f"audio_{uuid.uuid4()}.wav"
        filepath = os.path.join(TEMP_DIR, filename)
        audio_file.save(filepath)

        # Convert speech to text
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)  # Capture entire audio
            text = recognizer.recognize_google(audio_data, language=language)

        # Delete the temporary file
        os.remove(filepath)

        return jsonify({'transcribed_text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech and return an audio file."""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text']
    language = data.get('language', 'en')

    try:
        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)

        # Generate speech
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(filepath)

        return send_file(filepath, mimetype="audio/mpeg", as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    """Translate text from one language to another."""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')

    try:
        translation = translator.translate(data['text'], src=source_lang, dest=target_lang)
        return jsonify({
            'original_text': data['text'],
            'translated_text': translation.text,
            'source_language': translation.src,
            'target_language': translation.dest
        })
    except Exception as e:
        return jsonify({'error': str(e), 'original_text': data['text']}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Check if the service is running."""
    return jsonify({'status': 'healthy', 'message': 'Translation service is running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
