export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss', '@vite-pwa/nuxt'],
  tailwindcss: {
    exposeConfig: true,
  },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: (process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000').trim(),
    },
  },
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Penerjemah Kitab',
      short_name: 'KitabTerj',
      description: 'Terjemah Arab kata-per-kata — analisis, tashkeel, OCR, dan terjemahan seperti ulama membaca kitab',
      lang: 'id',
      theme_color: '#1a3a2a',
      background_color: '#f5f0e8',
      display: 'standalone',
      orientation: 'any',
      scope: '/',
      start_url: '/',
      categories: ['education', 'books', 'reference'],
      icons: [
        {
          src: '/icons/icon-192.png',
          sizes: '192x192',
          type: 'image/png',
          purpose: 'any maskable',
        },
        {
          src: '/icons/icon-512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable',
        },
      ],

    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
      navigateFallback: '/',
    },
    client: {
      installPrompt: true,
      periodicSyncForUpdates: 3600,
    },
    dev: true,
  },
  compatibilityDate: '2026-07-24',
})
