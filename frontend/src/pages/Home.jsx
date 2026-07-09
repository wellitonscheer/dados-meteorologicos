import { useState, useEffect, useRef } from "react";
import { getModels, sendMessageStream } from "../api.js";

// Formata os argumentos de uma tool de forma compacta: k=v, k=v
function formatVal(v) {
  if (typeof v === "string") return v.length > 24 ? `${v.slice(0, 24)}…` : v;
  if (v && typeof v === "object") return JSON.stringify(v);
  return String(v);
}
function formatArgs(args) {
  if (!args || typeof args !== "object") return "";
  return Object.entries(args)
    .map(([k, v]) => `${k}=${formatVal(v)}`)
    .join(", ");
}

export default function Home({ auth, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [models, setModels] = useState([]);
  const [model, setModel] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Carrega a lista de modelos disponíveis e seleciona o padrão do backend.
  useEffect(() => {
    getModels(auth.token)
      .then((data) => {
        setModels(data.models);
        setModel(data.default);
      })
      .catch(() => {
        // sem lista: o backend cai no modelo padrão ao enviar a mensagem
      });
  }, [auth.token]);

  // Atualiza a última mensagem (o balão do assistente em progresso) de forma imutável.
  function atualizarUltima(fn) {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const copia = prev.slice();
      copia[copia.length - 1] = fn(copia[copia.length - 1]);
      return copia;
    });
  }

  async function handleSend(e) {
    e.preventDefault();
    const content = text.trim();
    if (!content || sending) return;

    // Mensagem do usuário + balão do assistente "em progresso".
    setMessages((prev) => [
      ...prev,
      { from: "me", text: content },
      { from: "server", text: "", steps: [], streaming: true },
    ]);
    setText("");
    setSending(true);

    try {
      await sendMessageStream(content, auth.token, model, {
        onTool: ({ nome, argumentos }) =>
          atualizarUltima((m) => ({
            ...m,
            steps: [...m.steps, { nome, argumentos, estado: "rodando" }],
          })),
        onToolFim: ({ erro }) =>
          atualizarUltima((m) => {
            // marca a última tool ainda "rodando" como concluída
            const steps = m.steps.slice();
            for (let i = steps.length - 1; i >= 0; i--) {
              if (steps[i].estado === "rodando") {
                steps[i] = { ...steps[i], estado: erro ? "erro" : "ok" };
                break;
              }
            }
            return { ...m, steps };
          }),
        onText: (delta) =>
          atualizarUltima((m) => ({ ...m, text: m.text + delta })),
        onErro: (mensagem) =>
          atualizarUltima((m) => ({
            ...m,
            text: m.text ? `${m.text}\n\n${mensagem}` : mensagem,
            streaming: false,
          })),
        onFim: () => atualizarUltima((m) => ({ ...m, streaming: false })),
      });
    } catch (err) {
      atualizarUltima((m) => ({
        ...m,
        text: m.text ? `${m.text}\n\nErro: ${err.message}` : `Erro: ${err.message}`,
        streaming: false,
      }));
    } finally {
      // rede de segurança: garante que o balão não fique "streamando" pra sempre
      atualizarUltima((m) => (m.streaming ? { ...m, streaming: false } : m));
      setSending(false);
    }
  }

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Topo com usuário logado */}
      <header className="bg-white shadow-sm px-6 py-3 flex items-center justify-between gap-4">
        <span className="text-slate-700">
          Logado como <span className="font-semibold">{auth.username}</span>
        </span>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="hidden sm:inline">Modelo</span>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={models.length === 0}
              className="rounded-lg border border-slate-300 px-2 py-1 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          <button
            onClick={onLogout}
            className="text-sm rounded-lg border border-slate-300 px-3 py-1 text-slate-600 hover:bg-slate-50"
          >
            Sair
          </button>
        </div>
      </header>

      {/* Área do chat */}
      <main className="flex-1 min-h-0 overflow-y-auto p-4">
        <div className="max-w-2xl mx-auto space-y-3">
          {messages.length === 0 && (
            <p className="text-center text-slate-400 mt-10">
              Pergunte sobre os dados meteorológicos, a previsão do tempo ou a agenda.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.from === "me" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`rounded-2xl px-4 py-2 max-w-[75%] ${
                  m.from === "me"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-800 shadow-sm"
                }`}
              >
                {/* Transparência: tools chamadas (nome + argumentos) ao vivo */}
                {m.from === "server" && m.steps?.length > 0 && (
                  <div className="mb-2 space-y-1 border-b border-slate-100 pb-2">
                    {m.steps.map((s, si) => (
                      <div
                        key={si}
                        className="flex items-center gap-1.5 text-xs text-slate-500 font-mono"
                      >
                        <span aria-hidden>
                          {s.estado === "ok" ? "✓" : s.estado === "erro" ? "⚠" : "⏳"}
                        </span>
                        <span>
                          🔧 {s.nome}({formatArgs(s.argumentos)})
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="whitespace-pre-wrap">
                  {m.text}
                  {m.streaming && (
                    <span className="ml-0.5 animate-pulse text-slate-400">▌</span>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input de mensagem */}
      <form
        onSubmit={handleSend}
        className="bg-white border-t border-slate-200 px-4 py-3"
      >
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Digite uma mensagem..."
            className="flex-1 rounded-full border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={sending}
            className="rounded-full bg-blue-600 text-white px-5 py-2 font-medium hover:bg-blue-700 disabled:opacity-60"
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  );
}
