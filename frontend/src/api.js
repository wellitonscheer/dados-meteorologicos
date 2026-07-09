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

export async function getModels(token) {
  const res = await fetch(`${API_URL}/api/models`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Falha ao carregar modelos");
  }
  return res.json(); // { models: [{ id, label }], default }
}

export async function sendMessage(text, token, model) {
  const res = await fetch(`${API_URL}/api/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    // model vazio/undefined é omitido -> backend usa o modelo padrão
    body: JSON.stringify({ text, model: model || undefined }),
  });
  if (!res.ok) {
    throw new Error("Falha ao enviar mensagem");
  }
  return res.json(); // { reply }
}
