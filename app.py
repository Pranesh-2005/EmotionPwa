from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from deep_translator import GoogleTranslator  # For translation
from langdetect import detect                 # For language detection
import torch

app = Flask(__name__)
CORS(app)

# Load the model and tokenizer
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Define the emotion labels based on the model output
emotion_labels = {
    0: "Negative 😕",   # Index for negative sentiment
    1: "Neutral 😐",    # Index for neutral sentiment
    2: "Positive 🙂"     # Index for positive sentiment
}

# Initialize the deep-translator GoogleTranslator
translator = GoogleTranslator(source='auto', target='en')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.get_json()
    user_input = data.get('text', '')

    # Step 1: Detect the language of the input text using langdetect
    detected_language = detect(user_input)

    # Step 2: If the language is not English, translate it to English
    if detected_language != 'en':
        translated_text = translator.translate(user_input)
    else:
        translated_text = user_input

    # Step 3: Tokenize the translated text for sentiment analysis
    max_length = 512  # Maximum token length for the model
    inputs = tokenizer(translated_text, return_tensors="pt", truncation=True, padding=True, max_length=max_length)

    # Step 4: Perform sentiment inference
    with torch.no_grad():
        outputs = model(**inputs)

    # Get the predicted sentiment class
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=-1).item()

    # Step 5: Map the predicted class to an emotion label
    emotion = emotion_labels.get(predicted_class, "Unknown")

    # Return the original language, translated text, and detected sentiment
    return jsonify({
        "original_text": user_input,
        "translated_text": translated_text,
        "detected_language": detected_language,
        "predicted_sentiment": emotion
    })

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')  # Serve from the current directory

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=7070)
