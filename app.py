from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from langdetect import detect
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import uuid
import tempfile

app = Flask(__name__)
CORS(app)

# Initialize Google Translator
recognizer = sr.Recognizer()
try:
    translator = Translator()
except Exception as e:
    print(f"Error initializing translator: {e}")
    translator = None

TEMP_DIR = tempfile.gettempdir()

# Language mapping for compatibility
LANGUAGE_MAP = {
    'zh-cn': 'zh-CN',
    'zh-tw': 'zh-TW',
    'en': 'en',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'ja': 'ja',
    'ru': 'ru',
    'hi': 'hi'
}

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    language = data.get('language', 'en')
    
    try:
        # Generate a unique filename
        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Generate speech
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(filepath)
        
        # Return the audio file
        return send_file(
            filepath,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/supported_languages', methods=['GET'])
def get_supported_languages():
    try:
        # Return all languages supported by googletrans
        # Convert LANGUAGES to a regular dict for JSON serialization
        languages_dict = {k: v for k, v in LANGUAGES.items()}
        return jsonify({
            'languages': languages_dict,
            'status': 'success'
        })
    except Exception as e:
        print(f"Error in supported_languages: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/detect_language', methods=['POST'])
def detect_language():
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
   
    try:
        # Use langdetect to identify the language
        detected_lang = detect(text)
       
        # Map detected language to supported languages
        mapped_lang = LANGUAGE_MAP.get(detected_lang, detected_lang)
       
        return jsonify({
            'language': mapped_lang,
            'original_detected': detected_lang
        })
    except Exception as e:
        print(f"Error in detect_language: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/translate', methods=['POST'])
def translate_text():
    if translator is None:
        return jsonify({'error': 'Translator service not available'}), 503
    
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
   
    try:
        # Translate text
        translation = translator.translate(
            text,
            dest=target_lang
        )
       
        return jsonify({
            'original_text': text,
            'translated_text': translation.text,
            'source_language': translation.src,
            'target_language': translation.dest
        })
    except Exception as e:
        print(f"Error in translate_text: {e}")
        return jsonify({
            'error': str(e),
            'original_text': text
        }), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Translation service is running',
        'translator_available': translator is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
