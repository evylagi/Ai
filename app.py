from flask import Flask, render_template, request, jsonify
import requests
import os
import base64
from datetime import datetime

app = Flask(__name__)

# Get API key from environment variable (set in Railway)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AQ.Ab8RN6K53Ys32SQJ0LlC6QMYLtnxbqic_9-nWXT542qSdKFMGw')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        api_key = data.get('api_key', '').strip() or GEMINI_API_KEY

        if not api_key:
            return jsonify({'error': 'API key is required. Please enter your key or set GEMINI_API_KEY in Railway.'}), 400

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Call Gemini API
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent?key={api_key}'
        
        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }]
        }

        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            return jsonify({'error': f'API error: {error_msg}'}), response.status_code

        result = response.json()
        
        # Extract image data
        candidates = result.get('candidates', [])
        if not candidates:
            return jsonify({'error': 'No candidates in response'}), 400

        parts = candidates[0].get('content', {}).get('parts', [])
        image_base64 = None
        mime_type = 'image/png'

        for part in parts:
            if 'inlineData' in part:
                inline_data = part['inlineData']
                image_base64 = inline_data.get('data')
                mime_type = inline_data.get('mimeType', 'image/png')
                break

        if not image_base64:
            # Check if there's text response (safety block)
            text_parts = [p.get('text') for p in parts if 'text' in p]
            if text_parts:
                return jsonify({'error': f'No image generated. Response: {" ".join(text_parts)}'}), 400
            return jsonify({'error': 'No image data found in response'}), 400

        return jsonify({
            'success': True,
            'image_data': image_base64,
            'mime_type': mime_type
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
