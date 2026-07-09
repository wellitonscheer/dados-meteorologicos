// Em dev, o compose define VITE_API_URL=http://localhost:8000 (front e back em
// origens diferentes). Em produção o front é servido pelo nginx na MESMA origem
// que faz proxy de /api, então VITE_API_URL fica vazio e as chamadas são relativas.
const API_URL = import.meta.env.VITE_API_URL || "";

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

// Versão streaming (SSE) do envio de mensagem. Usa fetch + reader (não
// EventSource, que não permite header Authorization). `history` são os turnos
// anteriores ([{ role, text }]) reenviados a cada mensagem para o modelo ter o
// contexto da conversa. Vai chamando os callbacks conforme os eventos do agente
// chegam em tempo real:
//   onText(delta)            -> pedaço do texto da resposta
//   onTool({ nome, argumentos }) -> uma tool prestes a rodar
//   onToolFim({ nome, erro })    -> tool concluída (✓/⚠)
//   onErro(mensagem)         -> erro amigável (encerra)
//   onFim()                  -> fim da resposta
export async function sendMessageStream(text, token, model, history = [], handlers = {}) {
  const { onText, onTool, onToolFim, onErro, onFim } = handlers;

  const res = await fetch(`${API_URL}/api/message/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    // history = turnos anteriores (para o modelo ter o contexto da conversa)
    body: JSON.stringify({ text, model: model || undefined, history }),
  });
  if (!res.ok || !res.body) {
    throw new Error("Falha ao enviar mensagem");
  }

  const processarBloco = (bloco) => {
    // Um bloco SSE pode ter várias linhas; junta o conteúdo das linhas "data:".
    const dados = bloco
      .split("\n")
      .filter((l) => l.startsWith("data:"))
      .map((l) => l.slice(5).trim())
      .join("");
    if (!dados) return;
    let ev;
    try {
      ev = JSON.parse(dados);
    } catch {
      return; // ruído/bloco incompleto: ignora
    }
    switch (ev.tipo) {
      case "texto":
        onText?.(ev.delta || "");
        break;
      case "tool":
        onTool?.({ nome: ev.nome, argumentos: ev.argumentos || {} });
        break;
      case "tool_fim":
        onToolFim?.({ nome: ev.nome, erro: !!ev.erro });
        break;
      case "erro":
        onErro?.(ev.mensagem || "Erro ao consultar o Gemini.");
        break;
      case "fim":
        onFim?.();
        break;
      default:
        break;
    }
  };

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const bloco = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      processarBloco(bloco);
    }
  }
  // resto sem "\n\n" final
  if (buffer.trim()) processarBloco(buffer);
}
