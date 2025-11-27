document.getElementById("clientForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const clientID = document.getElementById("clientID").value.trim();
    const clientSecret = document.getElementById("clientSecret").value.trim();

    const response = await fetch("/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientID, clientSecret })
    });

    const data = await response.json();

    if (!response.ok) {
        alert("Erro: " + data.error);
        return;
    }

    // Se passou a validação, exibe tela de login de usuário
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("login-section").style.display = "block";
});


// Login do usuário
document.getElementById("userForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
        alert("Erro: " + data.error);
        return;
    }

    // Exibe o JWT gerado
    document.getElementById("login-section").style.display = "none";
    document.getElementById("token-section").style.display = "block";
    document.getElementById("jwtToken").innerText = data.token;
});
