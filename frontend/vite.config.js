import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Hosts liberados pelo dev server ao expor via túnel/reverse proxy
// (lista separada por vírgula em VITE_ALLOWED_HOSTS, ex.: agente.caie.dev).
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS || "")
  .split(",")
  .map((h) => h.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    allowedHosts,
  },
});
