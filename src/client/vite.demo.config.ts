import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'demo',
  base: './',
  publicDir: false,
  plugins: [react()],
  build: { outDir: '../dist-demo', emptyOutDir: false, sourcemap: false },
});
