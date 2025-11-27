import json
import time
import jwt
from flask import Flask, request, jsonify, render_template
from werkzeug.security import check_password_hash

app = Flask(__name__)

# ------------------------------
# CONFIG
# ------------------------------
JWT_SECRET = "MEGA-SECRET-KEY"
JWT_ALG = "HS256"
JWT_EXP_SECONDS = 3600  # 1h

# ------------------------------
# LOAD JSON FILES
# ------------------------------
with open("clients.json", "r", encoding="utf-8") as f:
    clients = json.load(f)

with open("users.json", "r", encoding="utf-8") as f:
    users = json.load(f)


# ------------------------------
# HOME PAGE
# ------------------------------
@app.route('/')
def index():
    return render_template("index.html")


# ------------------------------
# CLIENT AUTH (clientID + clientSecret)
# ------------------------------
@app.route('/auth', methods=['POST'])
def auth_client():
    data = request.get_json() or {}
    client_id = data.get("clientID")
    client_secret = data.get("clientSecret")

    if not client_id or not client_secret:
        return jsonify({"error": "clientID e clientSecret são obrigatórios"}), 400

    client = clients.get(client_id)

    if client and client.get("clientSecret") == client_secret:
        return jsonify({"ok": True, "client": client["name"]})

    return jsonify({"error": "clientID ou clientSecret inválidos"}), 401


# ------------------------------
# USER LOGIN → GERA JWT
# ------------------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Preencha username e senha"}), 400

    user = users.get(username)

    if not user:
        return jsonify({"error": "Usuário ou senha inválidos"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Usuário ou senha inválidos"}), 401

    # Criar JWT
    iat = int(time.time())
    exp = iat + JWT_EXP_SECONDS

    payload = {
        "sub": user.get("sub", "1234567890"),
        "name": user.get("name", username),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "iat": iat,
        "exp": exp
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

    return jsonify({"token": token})


# ------------------------------
# VALIDAR TOKEN
# ------------------------------
@app.route('/validate-token', methods=['POST'])
def validate_token():
    data = request.get_json() or {}
    token = data.get("token")

    if not token:
        return jsonify({"error": "token required"}), 400

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return jsonify({"valid": True, "payload": decoded})

    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "token expired"}), 401

    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401


# ------------------------------
# RENDER.COM EXECUTION
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
