// app.js
// Frontend integration with backend (Flask server at http://localhost:5000)
// - client auth (clientID + clientSecret)
// - user register / login -> JWT
// - products list
// - cart ops (requires JWT)
// - checkout

const API = "http://localhost:5000"; // ajuste se necessário

// runtime state
let CLIENT_ID = null;
let JWT = localStorage.getItem("jwt") || null;

// helper headers
function jsonHeaders() {
  return { "Content-Type": "application/json" };
}
function authHeaders() {
  if (!JWT) return jsonHeaders();
  return { "Content-Type": "application/json", "Authorization": "Bearer " + JWT };
}

// ---------- NAVIGATION ----------
function navigate(pageId) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const el = document.getElementById(pageId);
  if (!el) return console.warn("Página não encontrada:", pageId);
  el.classList.add("active");

  // lazy actions when showing a page
  if (pageId === "products-section") loadProducts();
  if (pageId === "cart") loadCart();
}

// ---------- TOAST (simples) ----------
function toast(msg, time = 1800) {
  const t = document.createElement("div");
  t.innerText = msg;
  Object.assign(t.style, {
    position: "fixed", right: "18px", bottom: "18px",
    background: "rgba(0,0,0,0.7)", color: "white", padding: "10px 14px",
    borderRadius: "10px", zIndex: 9999
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), time);
}

// ---------- PRODUCTS ----------
async function loadProducts() {
  try {
    const res = await fetch(`${API}/products`);
    const data = await res.json();
    // data may be {products: [...] } in some servers; handle both
    const products = Array.isArray(data) ? data : (data.products || []);
    const grid = document.getElementById("product-grid");
    grid.innerHTML = "";
    products.forEach(p => {
      const card = document.createElement("div");
      card.className = "product";
      card.innerHTML = `
        <img src="${p.img || p.image || p.img_url || 'https://via.placeholder.com/300?text=Produto'}" alt="${p.name}">
        <h3>${p.name}</h3>
        <div class="price">R$ ${Number(p.price).toFixed(2)}</div>
        <button data-id="${p.id}">Adicionar ao Carrinho</button>
      `;
      const btn = card.querySelector("button");
      btn.addEventListener("click", () => addToCart(p.id));
      grid.appendChild(card);
    });
  } catch (err) {
    console.error("Erro ao carregar produtos:", err);
    toast("Erro ao carregar produtos");
  }
}

// ---------- CLIENT AUTH (clientID + clientSecret) ----------
async function validateClient() {
  const clientID = document.getElementById("clientID").value.trim();
  const clientSecret = document.getElementById("clientSecret").value.trim();
  if (!clientID || !clientSecret) {
    toast("Preencha clientID e clientSecret");
    return;
  }

  try {
    const res = await fetch(`${API}/auth`, {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ clientID, clientSecret })
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>({error:'erro'}));
      document.getElementById("authMsg").innerText = err.error || (err.detail || "Erro ao validar");
      document.getElementById("authMsg").style.color = "salmon";
      return;
    }

    // success
    CLIENT_ID = clientID;
    document.getElementById("authMsg").innerText = "Aplicação validada ✅. Agora faça login do usuário.";
    document.getElementById("authMsg").style.color = "#7fffd4";
    toast("Aplicação validada");
    // go to login page
    setTimeout(()=>navigate("login"), 800);
  } catch (err) {
    console.error("validateClient error", err);
    document.getElementById("authMsg").innerText = "Erro de conexão";
    document.getElementById("authMsg").style.color = "salmon";
  }
}

// ---------- REGISTER ----------
async function doRegister() {
  const username = document.getElementById("regUser").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPass").value;

  if (!username || !email || !password) { toast("Preencha todos os campos"); return; }

  try {
    const res = await fetch(`${API}/register`, {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ username, password, email })
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || "Erro no registro");
      return;
    }
    toast("Conta criada com sucesso, faça login");
    // prefill login
    document.getElementById("loginUser").value = username;
    navigate("login");
  } catch (err) {
    console.error("doRegister", err);
    toast("Erro de conexão");
  }
}

// ---------- LOGIN ----------
async function doLogin() {
  // Ensure client validated
  if (!CLIENT_ID) {
    toast("Valide a aplicação antes (clientID/clientSecret)");
    navigate("appAuth");
    return;
  }

  const username = document.getElementById("loginUser").value.trim();
  const password = document.getElementById("loginPass").value;
  if (!username || !password) { toast("Usuário e senha obrigatórios"); return; }

  try {
    const res = await fetch(`${API}/login`, {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ clientID: CLIENT_ID, username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || data.detail || "Login falhou");
      return;
    }
    JWT = data.token;
    localStorage.setItem("jwt", JWT);
    toast("Login bem-sucedido");
    navigate("products-section");
    await loadCart(); // atualizar carrinho do servidor
  } catch (err) {
    console.error("doLogin", err);
    toast("Erro de conexão no login");
  }
}

// ---------- CART ----------
async function addToCart(product_id, qty = 1) {
  if (!JWT) {
    toast("Faça login para adicionar ao carrinho");
    navigate("login");
    return;
  }
  try {
    const res = await fetch(`${API}/cart`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ product_id, qty })
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || "Erro ao adicionar");
      if (res.status === 401) handleLogout();
      return;
    }
    toast("Adicionado ao carrinho");
    updateCartCountFromCart(data.cart || []);
    await loadCart(); // refresh UI
  } catch (err) {
    console.error("addToCart", err);
    toast("Erro de conexão");
  }
}

async function loadCart() {
  if (!JWT) {
    updateCartCountFromCart([]);
    document.getElementById("cart-list").innerHTML = "<p class='muted'>Faça login para ver o carrinho.</p>";
    return;
  }
  try {
    const res = await fetch(`${API}/cart`, {
      method: "GET",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || "Erro ao buscar carrinho");
      if (res.status === 401) handleLogout();
      return;
    }
    // show cart
    renderCart(data.cart || []);
    updateCartCountFromCart(data.cart || []);
  } catch (err) {
    console.error("loadCart", err);
    toast("Erro de conexão");
  }
}

function renderCart(cart) {
  const list = document.getElementById("cart-list");
  list.innerHTML = "";
  if (!cart || cart.length === 0) {
    list.innerHTML = "<p>Nenhum item no carrinho.</p>";
    return;
  }

  cart.forEach(it => {
    // product detail fetch — try to find in products displayed, else fetch product list
    // For simplicity, show id + qty
    const el = document.createElement("div");
    el.className = "cart-item";
    el.style.marginBottom = "8px";
    el.innerHTML = `<div style="flex:1">Produto ID: ${it.product_id} — Quantidade: ${it.qty}</div>
                    <div style="min-width:120px;text-align:right"><button onclick="changeQty(${it.product_id}, -1)">-</button>
                    <span style="padding:0 8px">${it.qty}</span>
                    <button onclick="changeQty(${it.product_id}, 1)">+</button></div>`;
    list.appendChild(el);
  });
}

async function changeQty(product_id, delta) {
  try {
    // get current cart, modify locally then PUT
    const resGet = await fetch(`${API}/cart`, { method: "GET", headers: authHeaders() });
    const dataGet = await resGet.json();
    if (!resGet.ok) { toast("Erro"); return; }
    const cart = dataGet.cart || [];
    const item = cart.find(i => i.product_id === product_id);
    if (!item && delta > 0) cart.push({ product_id, qty: delta });
    else if (item) item.qty = Math.max(0, item.qty + delta);
    // filter out qty==0
    const items = cart.filter(i => i.qty > 0);
    const res = await fetch(`${API}/cart`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ items })
    });
    const d = await res.json();
    if (!res.ok) { toast(d.error || "Erro ao atualizar"); return; }
    toast("Carrinho atualizado");
    renderCart(d.cart || []);
    updateCartCountFromCart(d.cart || []);
  } catch (err) {
    console.error("changeQty", err);
    toast("Erro de conexão");
  }
}

async function clearCart() {
  if (!JWT) { toast("Faça login antes"); return; }
  try {
    const res = await fetch(`${API}/cart`, { method: "DELETE", headers: authHeaders() });
    const d = await res.json();
    if (!res.ok) { toast(d.error || "Erro"); return; }
    toast("Carrinho esvaziado");
    renderCart([]);
    updateCartCountFromCart([]);
  } catch (err) {
    console.error("clearCart", err);
    toast("Erro de conexão");
  }
}

function updateCartCountFromCart(cart) {
  const count = (cart || []).reduce((s, i) => s + (i.qty || 0), 0);
  const el = document.getElementById("cart-count");
  if (el) el.innerText = count;
}

// ---------- CHECKOUT ----------
async function placeOrder() {
  if (!JWT) { toast("Faça login antes de finalizar"); navigate("login"); return; }
  try {
    const res = await fetch(`${API}/checkout`, { method: "POST", headers: authHeaders() });
    const d = await res.json();
    if (!res.ok) { toast(d.error || "Erro no checkout"); return; }
    toast("Pedido criado! ID: " + (d.order && d.order.id ? d.order.id : ""));
    // clear UI cart
    renderCart([]);
    updateCartCountFromCart([]);
    navigate("home");
  } catch (err) {
    console.error("placeOrder", err);
    toast("Erro de conexão no checkout");
  }
}

// ---------- LOGIN STATE ----------
function handleLogout() {
  JWT = null;
  localStorage.removeItem("jwt");
  CLIENT_ID = null;
  toast("Sessão expirada. Faça login novamente.");
  navigate("appAuth");
}

// ---------- INIT & EVENTS ----------
function attachEventHandlers() {
  // buttons
  const btnAuth = document.getElementById("btnAuthApp");
  if (btnAuth) btnAuth.addEventListener("click", validateClient);

  const btnLogin = document.getElementById("btnLogin");
  if (btnLogin) btnLogin.addEventListener("click", doLogin);

  const btnRegister = document.getElementById("btnRegister");
  if (btnRegister) btnRegister.addEventListener("click", doRegister);

  const confirmBtn = document.getElementById("confirmarPedido");
  if (confirmBtn) confirmBtn.addEventListener("click", placeOrder);

  // initial load
  loadProducts();
  // if JWT present, try loading cart
  if (JWT) {
    loadCart();
  } else {
    updateCartCountFromCart([]);
  }
}

// run when DOM loaded
document.addEventListener("DOMContentLoaded", attachEventHandlers);
