import { defineConfig } from "vite";
export default defineConfig({ base: "./", root: "app", clearScreen: false, server: { port: 1420, strictPort: true }, build: { outDir: "../dist", emptyOutDir: true, sourcemap: false } });
