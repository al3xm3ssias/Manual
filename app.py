import os
from flask import Flask, send_file, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def home():
    return "Servidor Flask rodando com sucesso!"

@app.route("/editor")
def editor():
    return send_file("editor.html")


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"}), 200


@app.route('/save-module', methods=['POST'])

def save_module():
    data     = request.get_json()
    group    = data.get('group', 'procedimentos')          # ex: "procedimentos"
    filename = data.get('filename', 'modulo.html')
    html     = data.get('html', '')

    # Garante que o filename termina em .html
    if not filename.endswith('.html'):
        filename += '.html'

    save_dir = os.path.join(BASE_DIR, 'modulos', group)
    os.makedirs(save_dir, exist_ok=True)

    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return jsonify({ 'ok': True, 'path': f'modulos/{group}/{filename}' })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)