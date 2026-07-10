import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getModels, sendMessageStream } from "../api.js";
import SidebarPlanilhas from "../components/SidebarPlanilhas.jsx";

// Plugins e componentes do markdown em escopo de módulo: evita recriar os
// objetos a cada delta de streaming (que dispararia re-parse desnecessário).
const remarkPlugins = [remarkGfm];

const mdComponents = {
  // links abrem em nova aba, com segurança
  a({ node, ...props }) {
    return <a {...props} target="_blank" rel="noopener noreferrer" />;
  },
  // tabela com rolagem horizontal dentro do balão estreito (max-w-[75%])
  table({ node, ...props }) {
    return (
      <div className="overflow-x-auto">
        <table {...props} />
      </div>
    );
  },
};

// Balão fixo de boas-vindas: fica fora do array `messages` de propósito, para
// nunca entrar no histórico reenviado ao modelo.
const MENSAGEM_BOAS_VINDAS = `Olá! 👋 Eu sou o assistente de dados meteorológicos dos produtores rurais. Consulto as planilhas de clima e de propriedades, a previsão do tempo e a agenda. Alguns exemplos do que você pode perguntar:

- "Como estão as condições climáticas na propriedade do João Silva?"
- "Qual a previsão do tempo para a Fazenda Sol Nascente amanhã?"
- "Quais produtores ficam em Pelotas e o que eles cultivam?"`;

// Rótulos amigáveis para as tools que o agente chama (fallback genérico para
// tool nova ainda sem rótulo).
const ROTULOS_TOOLS = {
  buscar_registros: "Consultando os dados climáticos",
  ler_registros: "Lendo a planilha de dados climáticos",
  buscar_propriedades: "Consultando produtores e propriedades",
  geocodificar_local: "Localizando coordenadas",
  previsao_tempo: "Buscando a previsão do tempo",
  listar_eventos: "Consultando a agenda",
};
const rotuloTool = (nome) => ROTULOS_TOOLS[nome] || `Executando ${nome}`;

// Consultas do agente dentro do balão: durante o streaming mostra só a
// atividade atual (evita empilhar linhas quando há várias chamadas); ao
// concluir, colapsa tudo numa linha discreta expansível.
function PassosTools({ steps, streaming }) {
  if (!steps?.length) return null;

  if (streaming) {
    const atual = steps[steps.length - 1];
    return (
      <div className="mb-2 flex items-center gap-2 border-b border-slate-100 pb-2 text-xs text-slate-500">
        {atual.estado === "rodando" ? (
          <span
            className="inline-block h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"
            aria-hidden
          />
        ) : (
          <span aria-hidden>{atual.estado === "erro" ? "⚠" : "✓"}</span>
        )}
        <span>{rotuloTool(atual.nome)}…</span>
        {steps.length > 1 && (
          <span className="text-slate-400">({steps.length}ª consulta)</span>
        )}
      </div>
    );
  }

  const falhas = steps.filter((s) => s.estado === "erro").length;
  return (
    <details className="mb-2 border-b border-slate-100 pb-2 text-xs text-slate-500">
      <summary className="cursor-pointer select-none hover:text-slate-700">
        {falhas > 0 ? "⚠" : "✓"}{" "}
        {steps.length === 1
          ? "1 consulta realizada"
          : `${steps.length} consultas realizadas`}
        {falhas > 0 && ` (${falhas} com falha)`}
      </summary>
      <ul className="mt-1.5 space-y-1 pl-4">
        {steps.map((s, si) => (
          <li key={si}>
            {s.estado === "erro" ? "⚠" : "✓"} {rotuloTool(s.nome)}
          </li>
        ))}
      </ul>
    </details>
  );
}

export default function Home({ auth, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [models, setModels] = useState([]);
  const [model, setModel] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

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

    // Histórico visível (turnos anteriores) para o modelo ter o contexto da conversa.
    // `messages` aqui ainda reflete só os turnos já concluídos — o setMessages abaixo é
    // assíncrono e o botão fica travado (`sending`) enquanto um envio está em curso.
    // Ignora balões vazios, em progresso ou que terminaram em erro.
    const history = messages
      .filter((m) => m.text?.trim() && !m.streaming && !m.erro)
      .map((m) => ({ role: m.from === "me" ? "user" : "assistant", text: m.text }));

    // Mensagem do usuário + balão do assistente "em progresso".
    setMessages((prev) => [
      ...prev,
      { from: "me", text: content },
      { from: "server", text: "", steps: [], streaming: true },
    ]);
    setText("");
    setSending(true);

    try {
      await sendMessageStream(content, auth.token, model, history, {
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
            erro: true, // não reenvia mensagem de erro como histórico
          })),
        onFim: () => atualizarUltima((m) => ({ ...m, streaming: false })),
      });
    } catch (err) {
      atualizarUltima((m) => ({
        ...m,
        text: m.text ? `${m.text}\n\nErro: ${err.message}` : `Erro: ${err.message}`,
        streaming: false,
        erro: true, // não reenvia mensagem de erro como histórico
      }));
    } finally {
      // rede de segurança: garante que o balão não fique "streamando" pra sempre
      atualizarUltima((m) => (m.streaming ? { ...m, streaming: false } : m));
      setSending(false);
      // devolve o foco (perdido quando o envio foi pelo clique no botão)
      inputRef.current?.focus();
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

      {/* Sidebar de planilhas + coluna do chat */}
      <div className="flex-1 min-h-0 flex">
        <SidebarPlanilhas token={auth.token} />
        {/* min-w-0: sem ele, tabelas nos balões estouram o flex */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Área do chat */}
          <main className="flex-1 min-h-0 overflow-y-auto p-4">
            <div className="max-w-2xl mx-auto space-y-3">
              {/* Boas-vindas fixas: fora de `messages`, nunca entram no histórico */}
              <div className="flex justify-start">
                <div className="rounded-2xl px-4 py-2 max-w-[75%] bg-white text-slate-800 shadow-sm">
                  <div className="prose prose-sm prose-slate max-w-none break-words">
                    <ReactMarkdown
                      remarkPlugins={remarkPlugins}
                      components={mdComponents}
                    >
                      {MENSAGEM_BOAS_VINDAS}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
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
                    {/* Transparência: consultas do agente, em linguagem amigável */}
                    {m.from === "server" && (
                      <PassosTools steps={m.steps} streaming={m.streaming} />
                    )}
                    {m.from === "server" ? (
                      <div className="prose prose-sm prose-slate max-w-none break-words prose-pre:whitespace-pre-wrap prose-pre:break-words">
                        <ReactMarkdown
                          remarkPlugins={remarkPlugins}
                          components={mdComponents}
                        >
                          {m.text}
                        </ReactMarkdown>
                        {m.streaming && (
                          <span className="animate-pulse text-slate-400">▌</span>
                        )}
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap break-words">{m.text}</div>
                    )}
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
                ref={inputRef}
                autoFocus
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
      </div>
    </div>
  );
}
