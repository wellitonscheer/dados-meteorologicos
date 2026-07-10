import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getModels, sendMessageStream } from "../api.js";
import SidebarPlanilhas from "../components/SidebarPlanilhas.jsx";
import {
  Brandmark,
  IconAlert,
  IconCheck,
  IconChevron,
  IconSend,
} from "../components/icons.jsx";

// Plugins e componentes do markdown em escopo de módulo: evita recriar os
// objetos a cada delta de streaming (que dispararia re-parse desnecessário).
const remarkPlugins = [remarkGfm];

const mdComponents = {
  // links abrem em nova aba, com segurança
  a({ node, ...props }) {
    return <a {...props} target="_blank" rel="noopener noreferrer" />;
  },
  // tabela com rolagem horizontal dentro do balão estreito (max-w-[80%])
  table({ node, ...props }) {
    return (
      <div className="overflow-x-auto">
        <table {...props} />
      </div>
    );
  },
};

// Classes do markdown renderizado dentro dos balões: hierarquia tintada com os
// tokens do app (evita o cinza/azul padrão do plugin typography).
const PROSE =
  "prose prose-sm max-w-none break-words prose-p:text-ink prose-li:text-ink prose-headings:text-ink prose-strong:text-ink prose-strong:font-semibold prose-a:text-primary prose-a:font-medium prose-code:text-ink prose-code:before:content-none prose-code:after:content-none prose-th:text-ink prose-td:text-ink-soft";

// Perguntas de exemplo mostradas no empty state (clicáveis, preenchem o input).
// Ficam fora de `messages` de propósito: são sugestões, nunca entram no histórico.
const EXEMPLOS = [
  "Como estão as condições climáticas na propriedade do João Silva?",
  "Qual a previsão do tempo para a Fazenda Sol Nascente amanhã?",
  "Quais produtores ficam em Pelotas e o que eles cultivam?",
];

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

// Ícone de estado de uma consulta (concluída / com falha), reutilizado nas duas
// visões do PassosTools.
function EstadoIcone({ estado, size = 13 }) {
  return estado === "erro" ? (
    <IconAlert size={size} className="shrink-0 text-warn" />
  ) : (
    <IconCheck size={size} className="shrink-0 text-ok" />
  );
}

// Empty state: apresenta o assistente e ensina o que perguntar. Os exemplos são
// botões que preenchem o input.
function EmptyState({ onPick }) {
  return (
    <div className="mx-auto flex min-h-full max-w-xl flex-col justify-center px-4 py-12">
      <span className="text-primary">
        <Brandmark size={26} />
      </span>
      <h2 className="mt-4 text-xl font-semibold tracking-tight text-ink">
        Como posso ajudar?
      </h2>
      <div className="mt-6 space-y-2">
        {EXEMPLOS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="group flex w-full items-center gap-3 rounded-field border border-line bg-surface px-4 py-3 text-left text-sm text-ink-soft transition-colors hover:border-primary/40 hover:text-ink"
          >
            <span className="flex-1">{q}</span>
            <IconChevron
              size={16}
              className="-rotate-90 shrink-0 text-ink-muted transition-transform group-hover:text-primary"
            />
          </button>
        ))}
      </div>
    </div>
  );
}

// Consultas do agente dentro do balão: durante o streaming mostra só a
// atividade atual (evita empilhar linhas quando há várias chamadas); ao
// concluir, colapsa tudo numa linha discreta expansível.
function PassosTools({ steps, streaming }) {
  if (!steps?.length) return null;

  if (streaming) {
    const atual = steps[steps.length - 1];
    return (
      <div className="mb-2 flex items-center gap-2 border-b border-line pb-2 text-xs text-ink-muted">
        {atual.estado === "rodando" ? (
          <span
            className="inline-block h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-line-strong border-t-primary motion-reduce:animate-none"
            aria-hidden
          />
        ) : (
          <EstadoIcone estado={atual.estado} size={14} />
        )}
        <span>{rotuloTool(atual.nome)}…</span>
        {steps.length > 1 && (
          <span className="text-ink-muted/70">({steps.length}ª consulta)</span>
        )}
      </div>
    );
  }

  const falhas = steps.filter((s) => s.estado === "erro").length;
  return (
    <details className="group mb-2 border-b border-line pb-2 text-xs text-ink-muted">
      <summary className="flex cursor-pointer list-none select-none items-center gap-1.5 transition-colors hover:text-ink-soft [&::-webkit-details-marker]:hidden">
        <IconChevron
          size={13}
          className="shrink-0 transition-transform group-open:rotate-180"
        />
        {falhas > 0 ? (
          <IconAlert size={13} className="shrink-0 text-warn" />
        ) : (
          <IconCheck size={13} className="shrink-0 text-ok" />
        )}
        <span>
          {steps.length === 1
            ? "1 consulta realizada"
            : `${steps.length} consultas realizadas`}
          {falhas > 0 && ` · ${falhas} com falha`}
        </span>
      </summary>
      <ul className="mt-2 space-y-1.5 pl-1">
        {steps.map((s, si) => (
          <li key={si} className="flex items-center gap-1.5">
            <EstadoIcone estado={s.estado} />
            <span>{rotuloTool(s.nome)}</span>
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

  // Preenche o input com um exemplo e devolve o foco.
  function usarExemplo(q) {
    setText(q);
    inputRef.current?.focus();
  }

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
    <div className="flex h-screen flex-col bg-app">
      {/* Topo: marca + modelo + usuário logado */}
      <header className="flex items-center justify-between gap-4 bg-header px-4 py-3 text-header-fg sm:px-6">
        <div className="flex min-w-0 items-center gap-2.5">
          <Brandmark size={22} className="shrink-0" />
          <div className="min-w-0 leading-tight">
            <div className="truncate text-sm font-semibold tracking-tight">
              Assistente Meteorológico
            </div>
            <div className="hidden text-xs text-header-soft sm:block">
              Clima e propriedades dos produtores
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <label className="flex items-center gap-2 text-sm text-header-soft">
            <span className="hidden sm:inline">Modelo</span>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={models.length === 0}
              className="rounded-field border border-white/20 bg-white/10 px-2.5 py-1.5 text-sm text-header-fg transition-colors focus:border-white/40 focus:outline-none disabled:opacity-60 [&>option]:bg-surface [&>option]:text-ink"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          <span className="hidden text-sm font-medium md:inline">
            {auth.username}
          </span>
          <button
            onClick={onLogout}
            className="rounded-field border border-white/20 px-3 py-1.5 text-sm transition-colors hover:bg-white/10"
          >
            Sair
          </button>
        </div>
      </header>

      {/* Sidebar de planilhas + coluna do chat */}
      <div className="flex min-h-0 flex-1">
        <SidebarPlanilhas token={auth.token} />
        {/* min-w-0: sem ele, tabelas nos balões estouram o flex */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Área do chat */}
          <main className="min-h-0 flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <EmptyState onPick={usarExemplo} />
            ) : (
              <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={`flex ${m.from === "me" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-bubble px-4 py-2.5 ${
                        m.from === "me"
                          ? "bg-primary text-primary-fg"
                          : "border border-line bg-surface text-ink"
                      }`}
                    >
                      {/* Transparência: consultas do agente, em linguagem amigável */}
                      {m.from === "server" && (
                        <PassosTools steps={m.steps} streaming={m.streaming} />
                      )}
                      {m.from === "server" ? (
                        <div
                          className={`${PROSE} prose-pre:whitespace-pre-wrap prose-pre:break-words`}
                        >
                          <ReactMarkdown
                            remarkPlugins={remarkPlugins}
                            components={mdComponents}
                          >
                            {m.text}
                          </ReactMarkdown>
                          {m.streaming && (
                            <span
                              className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse rounded-full bg-ink-muted align-middle motion-reduce:animate-none"
                              aria-hidden
                            />
                          )}
                        </div>
                      ) : (
                        <div className="whitespace-pre-wrap break-words">
                          {m.text}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            )}
          </main>

          {/* Input de mensagem */}
          <form
            onSubmit={handleSend}
            className="border-t border-line bg-surface px-4 py-3"
          >
            <div className="mx-auto flex max-w-2xl gap-2">
              <input
                ref={inputRef}
                autoFocus
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Digite uma mensagem…"
                className="flex-1 rounded-field border border-line bg-app px-4 py-2.5 text-ink placeholder:text-ink-muted transition-colors focus:border-primary focus:bg-surface focus:outline-none"
              />
              <button
                type="submit"
                disabled={sending}
                className="flex items-center gap-2 rounded-field bg-primary px-4 py-2.5 font-semibold text-primary-fg transition-colors hover:bg-primary-hover active:bg-primary-active disabled:cursor-not-allowed disabled:opacity-60"
              >
                <IconSend size={17} />
                <span className="hidden sm:inline">Enviar</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
