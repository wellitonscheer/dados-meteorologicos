import { useEffect, useState } from "react";
import { getPlanilhas } from "../api.js";

// Sidebar com as planilhas conectadas ao agente: link para a planilha real e
// estrutura expansível (colunas + dados de exemplo) para o usuário saber o que
// dá para perguntar. Some em telas pequenas (< 768px).
export default function SidebarPlanilhas({ token }) {
  const [planilhas, setPlanilhas] = useState([]);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    getPlanilhas(token)
      .then((data) => setPlanilhas(data.planilhas))
      .catch(() => setErro(true));
  }, [token]);

  return (
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
            <details className="mt-2">
              <summary className="cursor-pointer select-none text-xs text-slate-600 hover:text-slate-800">
                Ver estrutura e exemplos
              </summary>
              <p className="mt-2 mb-1 text-xs font-medium text-slate-600">
                Colunas
              </p>
              <div className="flex flex-wrap gap-1">
                {p.colunas.map((c) => (
                  <span
                    key={c}
                    className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-600"
                  >
                    {c}
                  </span>
                ))}
              </div>
              <p className="mt-2 mb-1 text-xs font-medium text-slate-600">
                Exemplos
              </p>
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="text-[11px] text-slate-600 whitespace-nowrap">
                  <thead>
                    <tr className="border-b border-slate-200 text-left">
                      {p.colunas.map((c) => (
                        <th key={c} className="px-2 py-1 font-medium">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {p.exemplos.map((linha, i) => (
                      <tr key={i} className="border-b border-slate-100 last:border-0">
                        {linha.map((valor, j) => (
                          <td key={j} className="px-2 py-1">
                            {valor}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </div>
        ))}
      </div>
    </aside>
  );
}
