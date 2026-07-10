import { useEffect, useRef, useState } from "react";
import { getPlanilhas } from "../api.js";
import { IconAlert, IconChevron, IconExternal } from "./icons.jsx";

// Largura-alvo do popover de exemplos (44rem); usada para posicioná-lo sem
// vazar da viewport.
const LARGURA_PAINEL = 704;

// Sidebar com as planilhas conectadas ao agente: link para a planilha real e
// um popover com amostra de dados que desce do próprio botão, para o usuário
// saber o que dá para perguntar. Some em telas pequenas (< 768px).
export default function SidebarPlanilhas({ token }) {
  const [planilhas, setPlanilhas] = useState([]);
  const [erro, setErro] = useState(false);
  // popover aberto: { planilha, top, left } — posição fixa calculada no clique
  // para o painel poder ser mais largo que a sidebar e flutuar sobre o chat
  const [aberta, setAberta] = useState(null);
  const painelRef = useRef(null);

  useEffect(() => {
    getPlanilhas(token)
      .then((data) => setPlanilhas(data.planilhas))
      .catch(() => setErro(true));
  }, [token]);

  // fecha o popover com Esc ou clique fora (sem camada bloqueando a página:
  // clicar no "Ver exemplos" de outra planilha já troca o painel num clique só)
  useEffect(() => {
    if (!aberta) return;
    const onKey = (e) => e.key === "Escape" && setAberta(null);
    const onDown = (e) => {
      if (painelRef.current?.contains(e.target)) return;
      if (e.target.closest("[data-exemplos-toggle]")) return; // o botão faz o próprio toggle
      setAberta(null);
    };
    window.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onDown);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onDown);
    };
  }, [aberta]);

  function alternarExemplos(p, e) {
    if (aberta?.planilha.id === p.id) {
      setAberta(null);
      return;
    }
    const r = e.currentTarget.getBoundingClientRect();
    // clampa a posição horizontal para o painel não vazar da tela
    const largura = Math.min(LARGURA_PAINEL, window.innerWidth - 32);
    const left = Math.max(16, Math.min(r.left, window.innerWidth - largura - 16));
    setAberta({ planilha: p, top: r.bottom + 6, left });
  }

  return (
    <>
      <aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-line bg-sidebar px-4 py-5 md:block lg:w-80">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-ink-muted">
            Planilhas conectadas
          </h2>
          {planilhas.length > 0 && (
            <span className="rounded-full bg-primary-tint px-2 py-0.5 text-[0.68rem] font-semibold text-primary">
              {planilhas.length}
            </span>
          )}
        </div>

        {erro && (
          <p className="flex items-start gap-1.5 text-xs text-ink-muted">
            <IconAlert size={14} className="mt-px shrink-0 text-warn" />
            Não foi possível carregar as planilhas.
          </p>
        )}

        <div className="divide-y divide-line">
          {planilhas.map((p) => {
            const ativa = aberta?.planilha.id === p.id;
            return (
              <div key={p.id} className="py-3.5 first:pt-0">
                <div className="flex items-center gap-2">
                  <span
                    className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                    aria-hidden
                  />
                  <p className="text-sm font-semibold text-ink">{p.nome}</p>
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-medium text-primary transition-colors hover:text-primary-hover"
                  >
                    Abrir
                    <IconExternal size={13} />
                  </a>
                  <button
                    type="button"
                    data-exemplos-toggle
                    onClick={(e) => alternarExemplos(p, e)}
                    aria-expanded={ativa}
                    className="inline-flex items-center gap-1 text-xs font-medium text-ink-soft transition-colors hover:text-ink"
                  >
                    Ver exemplos
                    <IconChevron
                      size={13}
                      className={`transition-transform ${ativa ? "rotate-180" : ""}`}
                    />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </aside>

      {/* Popover de exemplos: desce do botão clicado e flutua sobre o chat
          (position fixed para escapar do overflow da sidebar), largo o
          suficiente para a tabela quase não precisar de scroll lateral */}
      {aberta && (
        <div
          ref={painelRef}
          className="fixed z-50 max-h-[60vh] w-[44rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-card border border-line bg-popover shadow-popover"
          style={{ top: aberta.top, left: aberta.left }}
        >
          <div className="flex items-center justify-between gap-4 border-b border-line px-4 py-2.5">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">
                {aberta.planilha.nome}
              </p>
              <p className="text-xs text-ink-muted">Amostra de dados</p>
            </div>
            <a
              href={aberta.planilha.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-primary transition-colors hover:text-primary-hover"
            >
              Abrir no Sheets
              <IconExternal size={13} />
            </a>
          </div>
          <div className="max-h-[calc(60vh-3.5rem)] overflow-auto">
            <table className="w-full text-xs text-ink-soft tabular-nums">
              <thead className="sticky top-0 z-10 bg-popover">
                <tr className="border-b border-line text-left text-ink-muted">
                  {aberta.planilha.colunas.map((c) => (
                    <th
                      key={c}
                      className="whitespace-nowrap px-3 py-2 align-top font-semibold"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {aberta.planilha.exemplos.map((linha, i) => (
                  <tr
                    key={i}
                    className="border-b border-line/70 transition-colors last:border-0 hover:bg-app/70"
                  >
                    {linha.map((valor, j) => (
                      <td key={j} className="px-3 py-2 align-top">
                        {valor}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
