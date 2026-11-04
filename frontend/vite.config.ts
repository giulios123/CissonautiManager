/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
  build: { outDir: "dist" },
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test-setup.ts"] },
});
