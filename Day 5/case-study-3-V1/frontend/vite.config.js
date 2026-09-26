import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server runs on :5174 (see package.json "dev" script) — the default
// :5173 is used by an unrelated sibling project on this machine.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
  },
  preview: {
    port: 5174,
  },
})
