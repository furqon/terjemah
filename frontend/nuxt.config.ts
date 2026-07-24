export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  tailwindcss: {
    exposeConfig: true,
  },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: (process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000').trim(),
    },
  },
  compatibilityDate: '2026-07-24',
})
