from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import datetime
import os

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)  # libera CORS para todas as rotas

SECRET_KEY = "segredo_super_secreto"

# --- ARMAZENAMENTO SIMPLES (memória) ---
USERS = {}  # username -> {password, email}
CARTS = {}  # username -> [{product_id, qty}]
PRODUCTS = [
    {"id": 1, "name": "Câmera IP", "price": 199, "img": "https://via.placeholder.com/300?text=C%C3%A2mera"},
    {"id": 2, "name": "SSD 480GB", "price": 159, "img": "https://via.placeholder.com/300?text=SSD"},
    {"id": 3, "name": "Mouse Gamer", "price": 79, "img": "https://via.placeholder.com/300?text=Mouse"},
    {"id": 4, "name": "Teclado RGB", "price": 129, "img": "https://via.placeholder.com/300?text=Teclado"},
]

# --- ROTAS DE ARQUIVOS ---
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    if os.path.exists(path):
        return send_from_directory(".", path)
    return "Arquivo não encontrado", 404

# --- AUTENTICAÇÃO DA APLICAÇÃO ---
@app.route("/auth", methods=["POST"])
def auth():
    data = request.json
    client_id = data.get("clientID")
    client_secret = data.get("clientSecret")

    if client_id == "123" and client_secret == "abc":
        return jsonify({"status": "ok", "message": "Aplicação validada"})
    return jsonify({"status": "erro", "message": "Credenciais inválidas"}), 401

# --- REGISTRO ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"error": "Preencha todos os campos"}), 400
    if username in USERS:
        return jsonify({"error": "Usuário já existe"}), 400

    USERS[username] = {"password": password, "email": email, "role": "user"}
    CARTS[username] = []
    return jsonify({"message": "Conta criada com sucesso"}), 200

# --- LOGIN ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Login inválido"}), 401

    token = jwt.encode({
        "sub": username,
        "name": username,
        "email": user["email"],
        "role": user["role"],
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})

# --- PRODUTOS ---
@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(PRODUCTS)

# --- CARRINHO ---
def get_username_from_token(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data["sub"]
    except:
        return None

@app.route("/cart", methods=["GET", "POST", "PUT", "DELETE"])
def cart():
    username = get_username_from_token(request)
    if not username:
        return jsonify({"error": "Não autorizado"}), 401

    if request.method == "GET":
        return jsonify({"cart": CARTS.get(username, [])})

    elif request.method == "POST":
        data = request.json
        product_id = data.get("product_id")
        qty = data.get("qty", 1)
        cart = CARTS.get(username, [])
        for item in cart:
            if item["product_id"] == product_id:
                item["qty"] += qty
                break
        else:
            cart.append({"product_id": product_id, "qty": qty})
        CARTS[username] = cart
        return jsonify({"cart": cart})

    elif request.method == "PUT":
        data = request.json
        items = data.get("items", [])
        CARTS[username] = items
        return jsonify({"cart": CARTS[username]})

    elif request.method == "DELETE":
        CARTS[username] = []
        return jsonify({"cart": []})

# --- CHECKOUT ---
@app.route("/checkout", methods=["POST"])
def checkout():
    username = get_username_from_token(request)
    if not username:
        return jsonify({"error": "Não autorizado"}), 401
    # Aqui só limpamos o carrinho
    CARTS[username] = []
    return jsonify({"order": {"id": f"ORDER-{datetime.datetime.utcnow().timestamp()}"}})

# --- RUN ---
if __name__ == "__main__":
    app.run(debug=True)
