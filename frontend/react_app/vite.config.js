import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const rootDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: rootDir,
  plugins: [react()],
  build: {
    outDir: resolve(rootDir, "dist"),
    emptyOutDir: true,
    sourcemap: false,
    lib: {
      entry: resolve(rootDir, "src/main.jsx"),
      name: "RehabReactApp",
      formats: ["umd"],
      fileName: () => "rehab-react-app.umd.js",
    },
  },
});
