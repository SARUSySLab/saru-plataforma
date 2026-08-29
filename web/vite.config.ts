import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";

// A versao mostrada no rodape sai daqui, do package.json, e nao de uma string
// no componente: duas copias da versao desencontram no primeiro release.
const { version } = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));

// 5173 e 5175 ja estao ocupadas nesta maquina.
export default defineConfig({
  plugins: [react()],
  define: { __VERSAO__: JSON.stringify(version) },
  server: {
    port: 5177,
    proxy: {
      "/api": { target: "http://127.0.0.1:8010", changeOrigin: true },
    },
  },
});
