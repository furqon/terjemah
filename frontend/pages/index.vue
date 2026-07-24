<template>
  <div class="min-h-screen bg-amber-50">
    <header class="bg-emerald-800 text-white py-3 shadow">
      <div class="max-w-4xl mx-auto px-4">
        <h1 class="text-xl font-bold text-center">Penerjemah Kitab</h1>
        <p class="text-emerald-200 text-center text-xs mt-0.5">Analisis Kata Per Kata</p>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-4">
      <!-- Input -->
      <div class="bg-white rounded-lg shadow-sm border border-amber-100 p-4 mb-3">
        <label class="block text-sm font-semibold text-gray-600 mb-1">
          Teks Arab
        </label>
        <textarea
          v-model="inputText"
          placeholder="يكتب الطالب الدرس في المكتبة..."
          class="w-full h-24 p-3 border border-amber-200 rounded-lg text-base
                 focus:border-emerald-500 focus:outline-none resize-y
                 font-arabic transition-colors"
          dir="rtl"
        ></textarea>

        <button
          @click="analyze"
          :disabled="loading || !inputText.trim()"
          class="mt-2 w-full bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800
                 disabled:bg-gray-300 text-white font-semibold py-2 px-4 rounded-lg
                 transition-all duration-200 text-sm
                 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="flex items-center justify-center gap-1.5">
            <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Memproses
          </span>
          <span v-else>Analisis Teks</span>
        </button>
      </div>

      <!-- Error -->
      <Transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        leave-active-class="transition duration-200 ease-in"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div
          v-if="error"
          class="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded-lg mb-3 text-sm"
        >
          {{ error }}
        </div>
      </Transition>

      <!-- Result -->
      <Transition
        enter-active-class="transition duration-400 ease-out"
        enter-from-class="opacity-0 translate-y-3"
      >
        <div v-if="result" class="space-y-3">
          <!-- ── Harakat display ── -->
          <div class="bg-white rounded-lg shadow-sm border border-amber-100 p-4">
            <h2 class="text-base font-bold text-gray-700 mb-3 flex items-center gap-1.5">
              <span>Hasil Harakat</span>
              <span class="text-xs font-normal text-gray-400">({{ result.word_count }} kata)</span>
            </h2>

            <div class="grid md:grid-cols-2 gap-3">
              <!-- Before -->
              <div>
                <p class="text-xs text-gray-400 mb-1">Sebelum:</p>
                <div class="bg-gray-50 rounded border border-gray-100 p-3 text-right" dir="rtl">
                  <p class="text-lg">{{ result.original }}</p>
                </div>
              </div>

              <!-- After -->
              <div>
                <p class="text-xs text-gray-400 mb-1">Sesudah (dengan Harakat):</p>
                <div class="bg-emerald-50 border border-emerald-200 rounded p-3 text-right" dir="rtl">
                  <p class="text-lg text-emerald-700 font-arabic">{{ result.harakat }}</p>
                </div>
              </div>
            </div>

            <!-- Copy button -->
            <button
              @click="copyResult"
              class="mt-3 text-xs bg-amber-50 hover:bg-amber-100 text-amber-700
                     font-medium py-1.5 px-3 rounded transition-colors"
            >
              Salin Teks
            </button>
          </div>

          <!-- ── Word cards ── -->
          <div class="bg-white rounded-lg shadow-sm border border-amber-100 p-4">
            <h2 class="text-base font-bold text-gray-700 mb-3 flex items-center gap-1.5">
              <span>Kata Per Kata</span>
            </h2>

            <div class="flex flex-wrap gap-2 justify-center">
              <div
                v-for="(word, i) in result.words"
                :key="i"
                class="word-card bg-white border border-emerald-200 rounded-lg
                       p-2.5 text-center min-w-[105px] max-w-[140px] flex-1
                       hover:shadow transition-all duration-200
                       hover:border-emerald-400"
              >
                <!-- Arabic word -->
                <p class="text-xl font-arabic text-amber-900" dir="rtl">
                  {{ word.word }}
                </p>

                <!-- Lemma (small) -->
                <p class="text-xs font-semibold text-emerald-700 mt-1">{{ word.lemma }}</p>

                <!-- Root -->
                <p class="text-[10px] text-gray-400" v-if="word.root && word.root !== '—'">
                  {{ word.root }}
                </p>

                <!-- POS badge -->
                <span
                  class="inline-block mt-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                  :class="posBadgeClass(word.pos_type)"
                >
                  {{ word.pos_arabic }}
                </span>

                <!-- Translations: ID + EN -->
                <div class="mt-1 leading-tight">
                  <p v-if="word.gloss_id" class="text-[10px] font-medium text-emerald-600">
                    {{ word.gloss_id }}
                  </p>
                  <p v-if="word.gloss_en" class="text-[10px] text-gray-400 italic">
                    {{ word.gloss_en }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- ── Full translation ── -->
          <div v-if="translating" class="bg-white rounded-lg shadow-sm border border-amber-100 p-4">
            <h2 class="text-base font-bold text-gray-700 mb-2">Terjemahan Lengkap</h2>
            <p class="text-sm text-gray-400 italic">Menerjemahkan...</p>
          </div>
          <div v-if="translation" class="bg-white rounded-lg shadow-sm border border-amber-100 p-4">
            <h2 class="text-base font-bold text-gray-700 mb-2">Terjemahan Lengkap</h2>
            <div class="grid md:grid-cols-3 gap-3">
              <div>
                <p class="text-xs text-gray-400 mb-1">Teks Arab (dengan Harakat):</p>
                <div class="bg-gray-50 rounded border border-gray-100 p-3 text-right" dir="rtl">
                  <p class="text-base font-arabic text-amber-900">{{ result.harakat }}</p>
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Bahasa Indonesia:</p>
                <div class="bg-emerald-50 border border-emerald-200 rounded p-3">
                  <p class="text-sm text-emerald-800">{{ translation.translation_id }}</p>
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">English:</p>
                <div class="bg-blue-50 border border-blue-200 rounded p-3">
                  <p class="text-sm text-blue-800">{{ translation.translation_en }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ── Summary table ── -->
          <details class="bg-white rounded-lg shadow-sm border border-amber-100 p-3 group">
            <summary class="cursor-pointer text-emerald-700 hover:text-emerald-900
                           font-medium text-sm transition-colors
                           flex items-center gap-1.5">
              <span class="group-open:rotate-90 transition-transform duration-200 text-xs">▶</span>
              Detail Lengkap
            </summary>
            <div class="mt-2 overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="bg-amber-50 border-b border-amber-200">
                    <th class="p-2 text-left text-amber-700">#</th>
                    <th class="p-2 text-right text-amber-700">Arab</th>
                    <th class="p-2 text-left text-amber-700">Lemma</th>
                    <th class="p-2 text-left text-amber-700">Akar</th>
                    <th class="p-2 text-left text-amber-700">Jenis</th>
                    <th class="p-2 text-left text-amber-700">Arti</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(word, i) in result.words"
                    :key="'t'+i"
                    class="border-b border-amber-50 hover:bg-amber-50 transition-colors"
                  >
                    <td class="p-2 text-gray-400">{{ i + 1 }}</td>
                    <td class="p-2 font-arabic text-right text-base" dir="rtl">{{ word.word }}</td>
                    <td class="p-2 font-medium text-emerald-700">{{ word.lemma }}</td>
                    <td class="p-2 text-gray-400">{{ word.root !== '—' ? word.root : '—' }}</td>
                    <td class="p-2">
                      <span class="px-1.5 py-0.5 rounded-full text-[10px] font-bold" :class="posBadgeClass(word.pos_type)">
                        {{ word.pos_arabic }}
                      </span>
                    </td>
                    <td class="p-2">
                      <div class="text-emerald-700 text-[10px] font-medium">{{ word.gloss_id || '—' }}</div>
                      <div v-if="word.gloss_en" class="text-gray-400 text-[10px] italic">{{ word.gloss_en }}</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </Transition>
    </main>

    <footer class="text-center text-gray-400 text-xs py-4">
      Penerjemah Kitab
    </footer>
  </div>
</template>

<script setup lang="ts">
interface WordAnalysis {
  word: string
  lemma: string
  root: string
  pos_type: string
  pos_arabic: string
  gloss_id: string
  gloss_en: string
}

interface AnalyzeResponse {
  original: string
  harakat: string
  words: WordAnalysis[]
  word_count: number
}

const inputText = ref('')
const result = ref<AnalyzeResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const translating = ref(false)
const translation = ref<{ translation_id: string; translation_en: string } | null>(null)

const config = useRuntimeConfig()

const posColors: Record<string, string> = {
  noun: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
  verb: 'bg-orange-100 text-orange-700 hover:bg-orange-200',
  prep: 'bg-purple-100 text-purple-700 hover:bg-purple-200',
  conj: 'bg-purple-100 text-purple-700 hover:bg-purple-200',
  part: 'bg-gray-200 text-gray-700 hover:bg-gray-300',
  pron: 'bg-pink-100 text-pink-700 hover:bg-pink-200',
  adj: 'bg-green-100 text-green-700 hover:bg-green-200',
  adv: 'bg-teal-100 text-teal-700 hover:bg-teal-200',
  det: 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200',
  dem: 'bg-rose-100 text-rose-700 hover:bg-rose-200',
  neg: 'bg-red-100 text-red-700 hover:bg-red-200',
  interr: 'bg-cyan-100 text-cyan-700 hover:bg-cyan-200',
  num: 'bg-lime-100 text-lime-700 hover:bg-lime-200',
  noun_num: 'bg-lime-100 text-lime-700 hover:bg-lime-200',
  noun_quant: 'bg-lime-100 text-lime-700 hover:bg-lime-200',
  rel: 'bg-violet-100 text-violet-700 hover:bg-violet-200',
  noun_prop: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
  abbrev: 'bg-gray-200 text-gray-700 hover:bg-gray-300',
}

function posBadgeClass(type: string): string {
  return posColors[type] || 'bg-gray-100 text-gray-600 hover:bg-gray-200'
}

async function analyze() {
  loading.value = true
  error.value = null
  result.value = null

  try {
    const res = await fetch(`${config.public.apiBase}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value }),
    })
    if (!res.ok) throw new Error(`Error: ${res.status}`)
    result.value = await res.json()

    // Also request sentence translation (non-blocking)
    translateText(inputText.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Gagal menghubungi server'
  } finally {
    loading.value = false
  }
}

let _translateId = 0

async function translateText(text: string) {
  const requestId = ++_translateId
  translating.value = true
  translation.value = null
  try {
    const res = await fetch(`${config.public.apiBase}/api/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Error: ${res.status}` }))
      // Don't show error for translation — it's a bonus feature
      console.warn('Translation error:', err.detail)
      return
    }
    const data = await res.json()
    // Discard stale responses from previous requests
    if (requestId !== _translateId) return
    translation.value = { translation_id: data.translation_id, translation_en: data.translation_en }
  } catch (e) {
    // Translation is optional — silently fail
    console.warn('Translation unavailable:', e)
  } finally {
    translating.value = false
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

/* Staggered card animation on mount */
.word-card {
  animation: fadeSlideUp 0.4s ease-out both;
}

@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.word-card:nth-child(1) { animation-delay: 0.00s; }
.word-card:nth-child(2) { animation-delay: 0.05s; }
.word-card:nth-child(3) { animation-delay: 0.10s; }
.word-card:nth-child(4) { animation-delay: 0.15s; }
.word-card:nth-child(5) { animation-delay: 0.20s; }
.word-card:nth-child(6) { animation-delay: 0.25s; }
.word-card:nth-child(7) { animation-delay: 0.30s; }
.word-card:nth-child(8) { animation-delay: 0.35s; }
.word-card:nth-child(9) { animation-delay: 0.40s; }
.word-card:nth-child(10) { animation-delay: 0.45s; }
.word-card:nth-child(11) { animation-delay: 0.50s; }
.word-card:nth-child(12) { animation-delay: 0.55s; }
.word-card:nth-child(13) { animation-delay: 0.60s; }
.word-card:nth-child(14) { animation-delay: 0.65s; }
.word-card:nth-child(15) { animation-delay: 0.70s; }
</style>
