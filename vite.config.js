import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ command }) => {
  return {
    plugins: [react()],
    server: {
      host: true
    },
    preview: {
      port: 4173
    },
    base: command === "build" ? "/duckdb-react-demo/" : "/",
  };
});