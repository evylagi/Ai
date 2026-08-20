import os
import base64
from flask import Flask, render_template, request, jsonify
from google import genai
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Get API key from environment variable (optional - user can also provide their own)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AQ.Ab8RN6JCVBv_D9qceB2J-s8DIbQh_uHfnYuACo1XXQ0tJo2ong')

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

        # --- YOUR ORIGINAL CODE STARTS HERE ---
        # Configure the client with your API key
        client = genai.Client(api_key=api_key)

        print(f"Generating image for prompt: {prompt}")

        # Call the API to generate the image
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )

        # Extract image data from response
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]

        if not image_parts:
            return jsonify({'error': 'No image data found in response'}), 400

        # Get the image data
        image_data = image_parts[0]
        
        # Convert to base64 for sending to frontend
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Also save locally (optional)
        try:
            image = Image.open(BytesIO(image_data))
            image.save('generated_image.png')
        except Exception as e:
            print(f"Could not save image locally: {e}")

        return jsonify({
            'success': True,
            'image_data': image_base64,
            'mime_type': 'image/png'  # Gemini returns PNG
        })
        # --- YOUR ORIGINAL CODE ENDS HERE ---

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_key', methods=['GET'])
def check_key():
    """Check if API key is set in environment"""
    has_key = bool(GEMINI_API_KEY)
    return jsonify({'has_key': has_key})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
