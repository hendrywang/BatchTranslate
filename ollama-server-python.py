from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/generate"

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    
    # Forward the request to Ollama
    response = requests.post(OLLAMA_URL, json=data)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to get response from Ollama"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
