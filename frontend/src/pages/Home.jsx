import { useState, useEffect, useRef } from "react";
import { sendMessage } from "../api.js";

export default function Home({ auth, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const content = text.trim();
    if (!content) return;

    setMessages((prev) => [...prev, { from: "me", text: content }]);
    setText("");
    setSending(true);
    try {
      const data = await sendMessage(content, auth.token);
      setMessages((prev) => [...prev, { from: "server", text: data.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { from: "server", text: `Erro: ${err.message}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Topo com usuário logado */}
      <header className="bg-white shadow-sm px-6 py-3 flex items-center justify-between">
        <span className="text-slate-700">
          Logado como <span className="font-semibold">{auth.username}</span>
        </span>
        <button
          onClick={onLogout}
          className="text-sm rounded-lg border border-slate-300 px-3 py-1 text-slate-600 hover:bg-slate-50"
        >
          Sair
        </button>
      </header>

      {/* Área do chat */}
      <main className="flex-1 min-h-0 overflow-y-auto p-4">
        <div className="max-w-2xl mx-auto space-y-3">
          {messages.length === 0 && (
            <p className="text-center text-slate-400 mt-10">
              Envie uma mensagem — o servidor sempre responde "olá".
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
                {m.text}
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
