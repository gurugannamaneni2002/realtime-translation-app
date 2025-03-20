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

# Enable CORS for all routes
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

@app.route('/supported_languages', methods=['GET'])
def get_supported_languages():
    """Return a list of supported languages."""
    try:
        return jsonify({'languages': LANGUAGES, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/detect_language', methods=['POST', 'OPTIONS'])
def detect_language():
    """Detect the language of the given text."""
    if request.method == 'OPTIONS':
        return build_cors_preflight_response()

    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    try:
        detected_lang = detect(data['text'])
        mapped_lang = LANGUAGE_MAP.get(detected_lang, detected_lang)
        return jsonify({'language': mapped_lang, 'original_detected': detected_lang})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/translate', methods=['POST', 'OPTIONS'])
def translate_text():
    """Translate text from one language to another."""
    if request.method == 'OPTIONS':
        return build_cors_preflight_response()

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

# Handle CORS preflight
def build_cors_preflight_response():
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.after_request
def after_request(response):
    """Set CORS headers after every request."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
