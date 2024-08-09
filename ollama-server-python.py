from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434"

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=data, stream=True)
    
    def generate():
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        full_response += json_response['response']
                        yield json.dumps({"response": full_response}) + "\n"
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON: {line}")
        
        yield json.dumps({"response": full_response, "done": True}) + "\n"

    return Response(generate(), content_type='application/json')

@app.route('/models', methods=['GET'])
def get_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({"models": [model['name'] for model in models]})
        else:
            return jsonify({"error": "Failed to fetch models from Ollama"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)