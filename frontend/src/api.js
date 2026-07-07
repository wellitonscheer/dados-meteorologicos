const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function login(username, password) {
  const res = await fetch(`${API_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Falha no login");
  }
  return res.json(); // { access_token, token_type, username }
}

export async function sendMessage(text, token) {
  const res = await fetch(`${API_URL}/api/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error("Falha ao enviar mensagem");
  }
  return res.json(); // { reply }
}
