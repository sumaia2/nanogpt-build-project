"""
Flask backend for the AI-Powered Text Generation Portal.

Serves index.html and exposes a /generate endpoint that runs sample.py
as a subprocess and returns the generated text as JSON.

Place this file inside your myNanoGPT directory, alongside sample.py,
config.py, index.html, and the out-movies checkpoint folder.
"""

import subprocess
import re
from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/generate', methods=['POST'])
def generate():
    # Which trained model to sample from. Defaults to movies.
    # If you later add a twitter-trained model, its checkpoint folder
    # name goes here (e.g. "out-twitter").
    dataset = request.json.get('dataset', 'movies') if request.is_json else 'movies'
    out_dir = 'out-movies' if dataset == 'movies' else 'out-twitter'

    try:
        result = subprocess.run(
            ['uv', 'run', 'python', 'sample.py', f'--out_dir={out_dir}'],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Generation timed out'}), 504

    if result.returncode != 0:
        return jsonify({'error': result.stderr}), 500

    raw_output = result.stdout

    # sample.py prints some setup/status lines before the actual generated
    # text (e.g. "Overriding: out_dir = ...", "number of parameters: ...",
    # "Loading meta from ..."). Strip those known noise lines so only the
    # generated text remains.
    noise_patterns = [
        r'^Overriding:.*$',
        r'^number of parameters:.*$',
        r'^Loading meta from.*$',
    ]
    lines = raw_output.splitlines()
    cleaned_lines = [
        line for line in lines
        if not any(re.match(pattern, line) for pattern in noise_patterns)
    ]
    generated_text = '\n'.join(cleaned_lines).strip()

    # sample.py separates multiple samples with a line of dashes.
    # Since num_samples=1, just take everything before any such separator.
    generated_text = generated_text.split('---------------')[0].strip()

    return jsonify({'text': generated_text})


if __name__ == '__main__':
    app.run(debug=True)