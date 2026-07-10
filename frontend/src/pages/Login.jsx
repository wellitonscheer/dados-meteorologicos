import { useState } from "react";
import { login } from "../api.js";
import { Brandmark, IconAlert } from "../components/icons.jsx";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-app p-6">
      <div className="w-full max-w-sm">
        {/* Marca */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-2.5 text-primary">
            <Brandmark size={26} />
            <span className="text-lg font-semibold tracking-tight text-ink">
              Assistente Meteorológico
            </span>
          </div>
          <p className="mt-2 text-sm text-ink-muted">
            Clima e propriedades dos produtores rurais.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-card border border-line bg-surface p-7"
        >
          <h1 className="text-base font-semibold text-ink">Entrar na conta</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Informe suas credenciais para continuar.
          </p>

          <div className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <label
                htmlFor="usuario"
                className="block text-sm font-medium text-ink-soft"
              >
                Usuário
              </label>
              <input
                id="usuario"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-field border border-line bg-app px-3 py-2.5 text-ink placeholder:text-ink-muted transition-colors focus:border-primary focus:bg-surface focus:outline-none"
                autoFocus
                required
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="senha"
                className="block text-sm font-medium text-ink-soft"
              >
                Senha
              </label>
              <input
                id="senha"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-field border border-line bg-app px-3 py-2.5 text-ink placeholder:text-ink-muted transition-colors focus:border-primary focus:bg-surface focus:outline-none"
                required
              />
            </div>
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 flex items-start gap-2 rounded-field border border-danger/25 bg-danger-tint px-3 py-2.5 text-sm text-danger"
            >
              <IconAlert size={16} className="mt-px shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-field bg-primary py-2.5 font-semibold text-primary-fg transition-colors hover:bg-primary-hover active:bg-primary-active disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
