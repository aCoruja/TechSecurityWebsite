from flask import Flask, request, jsonify, send_from_directory
import jwt
import datetime

app = Flask(__name__)

SECRET_KEY = "segredo_super_secreto"

# --- DADOS SIMULADOS EM MEMÓRIA ---
USERS = {}  # username -> {password, email, role}
CARTS = {}  # username -> [{product_id, qty}]
PRODUCTS = [
    {"id": 1, "name": "Câmera IP", "price": 199, "img": "https://via.placeholder.com/300"},
    {"id": 2, "name": "SSD 480GB", "price": 159, "img": "https://via.placeholder.com/300"},
    {"id": 3, "name": "Mouse Gamer", "price": 79, "img": "https://via.placeholder.com/300"},
    {"id": 4, "name": "Teclado RGB", "price": 129, "img": "https://via.placeholder.com/300"}
]

VALID_CLIENTS = {"123": "abc"}  # clientID:clientSecret

# ---------------- ROTAS ----------------

# Servir index.html
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# Servir app.js
@app.route("/app.js")
def app_js():
    return send_from_directory(".", "app.js")

# Autenticação do client
@app.route("/auth", methods=["POST"])
def auth_app():
    data = request.json or {}
    clientID = data.get("clientID")
    clientSecret = data.get("clientSecret")
    if VALID_CLIENTS.get(clientID) == clientSecret:
        return jsonify({"status":"ok","message":"Aplicação autenticada"})
    return jsonify({"status":"erro","message":"Credenciais inválidas"}), 401

# Registro de usuário
@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    if not username or not password or not email:
        return jsonify({"error":"Preencha todos os campos"}), 400
    if username in USERS:
        return jsonify({"error":"Usuário já existe"}), 400
    USERS[username] = {"password": password, "email": email, "role": "user"}
    CARTS[username] = []
    return jsonify({"status":"ok","message":"Conta criada"})

# Login de usuário -> JWT
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    clientID = data.get("clientID")
    username = data.get("username")
    password = data.get("password")
    if VALID_CLIENTS.get(clientID) is None:
        return jsonify({"error":"Client não autorizado"}), 401
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error":"Login inválido"}), 401
    token = jwt.encode(
        {
            "sub": username,
            "name": username,
            "email": user["email"],
            "role": user["role"],
            "iat": datetime.datetime.utcnow().timestamp(),
            "exp": (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timestamp()
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return jsonify({"token": token})

# Listar produtos
@app.route("/products", methods=["GET"])
def products():
    return jsonify(PRODUCTS)

# ---------- JWT helper ----------
def decode_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

# ---------- CARRINHO ----------
@app.route("/cart", methods=["GET", "POST", "PUT", "DELETE"])
def cart():
    payload = decode_token(request.headers.get("Authorization"))
    if not payload:
        return jsonify({"error":"Token inválido"}), 401
    username = payload["sub"]
    user_cart = CARTS.get(username, [])

    if request.method == "GET":
        return jsonify({"cart": user_cart})

    data = request.json or {}
    if request.method == "POST":
        product_id = data.get("product_id")
        qty = data.get("qty", 1)
        for item in user_cart:
            if item["product_id"] == product_id:
                item["qty"] += qty
                break
        else:
            user_cart.append({"product_id": product_id, "qty": qty})
        CARTS[username] = user_cart
        return jsonify({"cart": user_cart})

    if request.method == "PUT":
        items = data.get("items", [])
        CARTS[username] = [i for i in items if i.get("qty",0)>0]
        return jsonify({"cart": CARTS[username]})

    if request.method == "DELETE":
        CARTS[username] = []
        return jsonify({"cart": []})

# ---------- CHECKOUT ----------
@app.route("/checkout", methods=["POST"])
def checkout():
    payload = decode_token(request.headers.get("Authorization"))
    if not payload:
        return jsonify({"error":"Token inválido"}), 401
    username = payload["sub"]
    CARTS[username] = []
    order_id = datetime.datetime.utcnow().timestamp()
    return jsonify({"order": {"id": int(order_id)}})

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
