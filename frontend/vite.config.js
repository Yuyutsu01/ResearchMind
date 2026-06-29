import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Configure Vite to load React plugin and bind to correct container ports
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // Needed for Docker network routing
  }
});
