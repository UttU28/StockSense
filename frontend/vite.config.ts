import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/v1": {
        target: "http://localhost:5000",
        changeOrigin: true,
        timeout: 120000,
        configure: (proxy) => {
          proxy.on("error", (err: Error) => {
            console.warn("[proxy] Backend connection failed - is it running on port 5000?", err.message);
          });
        },
      },
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
        timeout: 60000,
        configure: (proxy) => {
          proxy.on("error", (err) => {
            console.warn("[proxy] Backend connection failed - is it running on port 5000?", err.message);
          });
        },
      },
      "/auth": {
        target: "http://localhost:5000",
        changeOrigin: true,
        timeout: 30000,
        configure: (proxy) => {
          proxy.on("error", (err) => {
            console.warn("[proxy] Backend connection failed - is it running on port 5000?", err.message);
          });
        },
      },
      "/chart_img": { target: "http://localhost:5000", changeOrigin: true, timeout: 30000 },
      "/chart_v2": { target: "http://localhost:5000", changeOrigin: true, timeout: 30000 },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "src"),
    },
  },
  build: {
    outDir: path.resolve(import.meta.dirname, "dist"),
    emptyOutDir: true,
  },
});
