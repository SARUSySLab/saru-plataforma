import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 5173 e 5175 ja estao ocupadas nesta maquina.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5177,
    proxy: {
      "/api": { target: "http://127.0.0.1:8010", changeOrigin: true },
    },
  },
});
