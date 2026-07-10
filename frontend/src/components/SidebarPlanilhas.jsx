import { useEffect, useRef, useState } from "react";
import { getPlanilhas } from "../api.js";

// Sidebar com as planilhas conectadas ao agente: link para a planilha real e
// um dropdown com dados de exemplo que desce do próprio botão, para o usuário
// saber o que dá para perguntar. Some em telas pequenas (< 768px).
export default function SidebarPlanilhas({ token }) {
  const [planilhas, setPlanilhas] = useState([]);
  const [erro, setErro] = useState(false);
  // dropdown aberto: { planilha, top, left } — posição fixa calculada no clique
  // para o painel poder ser mais largo que a sidebar e flutuar sobre o chat
  const [aberta, setAberta] = useState(null);
  const painelRef = useRef(null);

  useEffect(() => {
    getPlanilhas(token)
      .then((data) => setPlanilhas(data.planilhas))
      .catch(() => setErro(true));
  }, [token]);

  // fecha o dropdown com Esc ou clique fora (sem camada bloqueando a página:
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
    setAberta({ planilha: p, top: r.bottom + 6, left: r.left });
  }

  return (
    <>
      <aside className="hidden md:block w-72 lg:w-80 shrink-0 overflow-y-auto bg-white border-r border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">
          📊 Planilhas conectadas
        </h2>
        {erro && (
          <p className="text-xs text-slate-400">
            Não foi possível carregar as planilhas.
          </p>
        )}
        <div className="space-y-3">
          {planilhas.map((p) => (
            <div
              key={p.id}
              className="rounded-xl border border-slate-200 bg-slate-50 p-3"
            >
              <p className="text-sm font-medium text-slate-800">{p.nome}</p>
              <p className="mt-0.5 text-xs text-slate-500">{p.descricao}</p>
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline"
              >
                Abrir no Google Sheets ↗
              </a>
              <button
                type="button"
                data-exemplos-toggle
                onClick={(e) => alternarExemplos(p, e)}
                className="mt-1 block text-xs text-slate-600 hover:text-slate-800 hover:underline"
              >
                Ver exemplos {aberta?.planilha.id === p.id ? "▴" : "▾"}
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Dropdown de exemplos: desce do botão clicado e flutua sobre o chat
          (position fixed para escapar do overflow da sidebar), largo o
          suficiente para a tabela quase não precisar de scroll lateral */}
      {aberta && (
          <div
            ref={painelRef}
            className="fixed z-50 w-[52rem] max-w-[calc(100vw-4rem)] max-h-[60vh] overflow-y-auto rounded-xl border border-slate-200 bg-white p-2 shadow-xl"
            style={{ top: aberta.top, left: aberta.left }}
          >
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full text-xs text-slate-600">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-left">
                    {aberta.planilha.colunas.map((c) => (
                      <th key={c} className="px-2 py-1.5 font-medium align-top">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {aberta.planilha.exemplos.map((linha, i) => (
                    <tr key={i} className="border-b border-slate-100 last:border-0">
                      {linha.map((valor, j) => (
                        <td key={j} className="px-2 py-1.5 align-top">
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
