import { useEffect, useState } from "react";
import { getPlanilhas } from "../api.js";

// Sidebar com as planilhas conectadas ao agente: link para a planilha real e
// um painel flutuante com dados de exemplo, para o usuário saber o que dá
// para perguntar. Some em telas pequenas (< 768px).
export default function SidebarPlanilhas({ token }) {
  const [planilhas, setPlanilhas] = useState([]);
  const [erro, setErro] = useState(false);
  const [aberta, setAberta] = useState(null); // planilha exibida no painel de exemplos

  useEffect(() => {
    getPlanilhas(token)
      .then((data) => setPlanilhas(data.planilhas))
      .catch(() => setErro(true));
  }, [token]);

  // fecha o painel com Esc
  useEffect(() => {
    if (!aberta) return;
    const onKey = (e) => e.key === "Escape" && setAberta(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [aberta]);

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
                onClick={() => setAberta(p)}
                className="mt-1 block text-xs text-slate-600 hover:text-slate-800 hover:underline"
              >
                Ver exemplos
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Painel flutuante de exemplos: sobrepõe o chat, largo o bastante para
          a tabela quase não precisar de scroll lateral */}
      {aberta && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-6"
          onClick={() => setAberta(null)}
        >
          <div
            className="w-full max-w-4xl max-h-[80vh] overflow-y-auto rounded-xl bg-white p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between gap-4">
              <h3 className="text-sm font-semibold text-slate-800">
                {aberta.nome} — exemplos de dados
              </h3>
              <button
                type="button"
                onClick={() => setAberta(null)}
                aria-label="Fechar"
                className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
              >
                ✕
              </button>
            </div>
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full text-xs text-slate-600">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-left">
                    {aberta.colunas.map((c) => (
                      <th key={c} className="px-2 py-1.5 font-medium align-top">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {aberta.exemplos.map((linha, i) => (
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
        </div>
      )}
    </>
  );
}
