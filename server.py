from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import datetime
import os

app = Flask(__name__, static_folder="")  # serve arquivos estáticos do mesmo diretório
CORS(app)  # libera CORS para todas as rotas

SECRET_KEY = "segredo_super_secreto"

# --- ROTA PRINCIPAL (SERVIR HTML) ---
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# --- ROTA PARA SERVIR ARQUIVOS ESTÁTICOS (app.js, css, imagens, etc) ---
@app.route("/<path:path>")
def static_files(path):
    if os.path.exists(path):
        return send_from_directory(".", path)
    return "Arquivo não encontrado", 404


# --- AUTENTICAÇÃO DE APLICAÇÃO ---
@app.route("/auth", methods=["POST"])
def auth_app():
    data = request.json
    client_id = data.get("clientID")
    client_secret = data.get("clientSecret")

    if client_id == "123" and client_secret == "abc":
        return jsonify({"status": "ok", "message": "Autenticado"})
    return jsonify({"status": "erro", "message": "Credenciais inválidas"}), 401


# --- LOGIN DE USUÁRIO / JWT ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    client_id = data.get("clientID")  # enviado pelo front
    username = data.get("username")
    password = data.get("password")

    # você pode validar client_id se quiser
    if username == "admin" and password == "123":
        token = jwt.encode(
            {"user": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"token": token})

    return jsonify({"error": "login inválido"}), 401


# --- LISTA DE PRODUTOS ---
@app.route("/products", methods=["GET"])
def products():
    lista = [
        {"id": 1, "name": "Câmera IP", "price": 199, "img": "https://via.placeholder.com/300?text=Câmera+IP"},
        {"id": 2, "name": "SSD 480GB", "price": 159, "img": "https://via.placeholder.com/300?text=SSD+480GB"},
        {"id": 3, "name": "Mouse Gamer", "price": 79, "img": "https://via.placeholder.com/300?text=Mouse+Gamer"},
        {"id": 4, "name": "Teclado RGB", "price": 129, "img": "https://via.placeholder.com/300?text=Teclado+RGB"},
    ]
    return jsonify({"products": lista})


# --- CARRINHO SIMPLES EM MEMÓRIA ---
carts = {}  # {token: [{product_id, qty}, ...]}

def verify_jwt(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user"]
    except:
        return None


@app.route("/cart", methods=["GET", "POST", "PUT", "DELETE"])
def cart_ops():
    user = verify_jwt(request)
    if not user:
        return jsonify({"error": "não autorizado"}), 401

    if user not in carts:
        carts[user] = []

    if request.method == "GET":
        return jsonify({"cart": carts[user]})

    data = request.json

    if request.method == "POST":
        # adicionar item
        product_id = data.get("product_id")
        qty = data.get("qty", 1)
        found = next((i for i in carts[user] if i["product_id"] == product_id), None)
        if found:
            found["qty"] += qty
        else:
            carts[user].append({"product_id": product_id, "qty": qty})
        return jsonify({"cart": carts[user]})

    if request.method == "PUT":
        # atualizar carrinho
        items = data.get("items", [])
        carts[user] = items
        return jsonify({"cart": carts[user]})

    if request.method == "DELETE":
        carts[user] = []
        return jsonify({"cart": []})


# --- CHECKOUT SIMPLES ---
@app.route("/checkout", methods=["POST"])
def checkout():
    user = verify_jwt(request)
    if not user:
        return jsonify({"error": "não autorizado"}), 401

    cart = carts.get(user, [])
    if not cart:
        return jsonify({"error": "carrinho vazio"}), 400

    # aqui poderia integrar pagamento, etc
    order_id = int(datetime.datetime.utcnow().timestamp())
    carts[user] = []  # limpa carrinho
    return jsonify({"order": {"id": order_id, "items": cart}})


# --- EXECUÇÃO NO RENDER ---
if __name__ == "__main__":
    app.run(port=5000,debug=True)
