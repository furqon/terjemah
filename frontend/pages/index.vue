<template>
  <div class="min-h-screen bg-amber-50">
    <header class="bg-emerald-800 text-white py-6 shadow-lg">
      <div class="max-w-4xl mx-auto px-4">
        <h1 class="text-3xl font-bold text-center">📖 Penerjemah Kitab</h1>
        <p class="text-emerald-200 text-center mt-1">Langkah 1: Tashkeel (Harakat)</p>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- Input -->
      <div class="bg-white rounded-xl shadow-md p-6 mb-6">
        <label class="block text-lg font-semibold text-gray-700 mb-2">
          Masukkan teks Arab:
        </label>
        <textarea
          v-model="inputText"
          placeholder="يكتب الطالب الدرس في المكتبة..."
          class="w-full h-32 p-4 border-2 border-amber-200 rounded-lg text-lg
                 focus:border-emerald-500 focus:outline-none resize-y
                 font-arabic"
          dir="rtl"
        ></textarea>

        <button
          @click="getTashkeel"
          :disabled="loading || !inputText.trim()"
          class="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300
                 text-white font-bold py-3 px-6 rounded-lg transition-colors
                 text-lg"
        >
          <span v-if="loading">⏳ Memproses...</span>
          <span v-else>🌟 Beri Harakat</span>
        </button>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6"
      >
        {{ error }}
      </div>

      <!-- Result -->
      <div v-if="result" class="bg-white rounded-xl shadow-md p-6">
        <h2 class="text-xl font-bold text-gray-700 mb-4">✅ Hasil</h2>

        <div class="grid md:grid-cols-2 gap-6">
          <!-- Before -->
          <div>
            <p class="text-sm text-gray-500 mb-2">Sebelum:</p>
            <div
              class="bg-gray-50 rounded-lg p-4 text-right"
              dir="rtl"
            >
              <p class="text-2xl">{{ result.original }}</p>
            </div>
          </div>

          <!-- After -->
          <div>
            <p class="text-sm text-gray-500 mb-2">Sesudah (dengan Harakat):</p>
            <div
              class="bg-emerald-50 border-2 border-emerald-200 rounded-lg p-4 text-right"
              dir="rtl"
            >
              <p class="text-2xl text-emerald-700 font-arabic">{{ result.harakat }}</p>
            </div>
          </div>
        </div>

        <!-- Copy button -->
        <button
          @click="copyResult"
          class="mt-4 bg-amber-100 hover:bg-amber-200 text-amber-800
                 font-medium py-2 px-4 rounded-lg transition-colors"
        >
          📋 Salin Teks
        </button>
      </div>
    </main>

    <footer class="text-center text-gray-400 text-sm py-6">
      Penerjemah Kitab — Dibangun langkah demi langkah
    </footer>
  </div>
</template>

<script setup lang="ts">
const inputText = ref('')
const result = ref<{ original: string; harakat: string } | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const config = useRuntimeConfig()

async function getTashkeel() {
  loading.value = true
  error.value = null
  result.value = null

  try {
    const res = await fetch(`${config.public.apiBase}/api/tashkeel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value }),
    })
    if (!res.ok) throw new Error(`Error: ${res.status}`)
    result.value = await res.json()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Gagal menghubungi server'
  } finally {
    loading.value = false
  }
}

async function copyResult() {
  if (result.value?.harakat) {
    await navigator.clipboard.writeText(result.value.harakat)
    alert('Teks berhasil disalin!')
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');

.font-arabic {
  font-family: 'Amiri', 'Traditional Arabic', serif;
}
</style>
