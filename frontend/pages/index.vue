<template>
  <div class="min-h-screen bg-amber-50">
    <header class="bg-emerald-800 text-white py-6 shadow-lg">
      <div class="max-w-4xl mx-auto px-4">
        <h1 class="text-3xl font-bold text-center">📖 Penerjemah Kitab</h1>
        <p class="text-emerald-200 text-center mt-1">Langkah 4: Analisis Kata Per Kata</p>
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
                 font-arabic transition-colors"
          dir="rtl"
        ></textarea>

        <button
          @click="analyze"
          :disabled="loading || !inputText.trim()"
          class="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800
                 disabled:bg-gray-300 text-white font-bold py-3 px-6 rounded-lg
                 transition-all duration-200 text-lg
                 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Memproses...
          </span>
          <span v-else>🌟 Analisis Teks</span>
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
          class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6"
        >
          {{ error }}
        </div>
      </Transition>

      <!-- Result -->
      <Transition
        enter-active-class="transition duration-500 ease-out"
        enter-from-class="opacity-0 translate-y-4"
      >
        <div v-if="result" class="space-y-6">
          <!-- ── Harakat display ── -->
          <div class="bg-white rounded-xl shadow-md p-6">
            <h2 class="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
              <span>✅ Hasil Harakat</span>
              <span class="text-sm font-normal text-gray-400">({{ result.word_count }} kata)</span>
            </h2>

            <div class="grid md:grid-cols-2 gap-6">
              <!-- Before -->
              <div>
                <p class="text-sm text-gray-500 mb-2">Sebelum:</p>
                <div class="bg-gray-50 rounded-lg p-4 text-right" dir="rtl">
                  <p class="text-2xl">{{ result.original }}</p>
                </div>
              </div>

              <!-- After -->
              <div>
                <p class="text-sm text-gray-500 mb-2">Sesudah (dengan Harakat):</p>
                <div class="bg-emerald-50 border-2 border-emerald-200 rounded-lg p-4 text-right" dir="rtl">
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

          <!-- ── Word cards ── -->
          <div class="bg-white rounded-xl shadow-md p-6">
            <h2 class="text-xl font-bold text-gray-700 mb-6 flex items-center gap-2">
              <span>📝 Analisis Kata Per Kata</span>
            </h2>

            <div class="flex flex-wrap gap-4 justify-center">
              <div
                v-for="(word, i) in result.words"
                :key="i"
                class="word-card bg-white border-2 border-emerald-200 rounded-xl
                       p-4 text-center min-w-[130px] max-w-[160px] flex-1
                       shadow-sm hover:shadow-lg transition-all duration-300
                       hover:-translate-y-1 hover:border-emerald-400"
              >
                <!-- Word number badge -->
                <div class="text-xs text-gray-400 mb-1">#{{ i + 1 }}</div>

                <!-- Arabic word (large) -->
                <p class="text-2xl font-arabic text-amber-900 mb-2" dir="rtl">
                  {{ word.word }}
                </p>

                <!-- Divider -->
                <div class="border-t border-amber-100 my-2"></div>

                <!-- Lemma -->
                <p class="text-sm font-semibold text-emerald-700">{{ word.lemma }}</p>

                <!-- Root -->
                <p class="text-xs text-gray-400 mb-2" v-if="word.root && word.root !== '—'">
                  (akar: {{ word.root }})
                </p>

                <!-- POS badge -->
                <span
                  class="inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-bold
                         transition-colors duration-200"
                  :class="posBadgeClass(word.pos_type)"
                >
                  {{ word.pos_arabic }}
                </span>

                <!-- Gloss -->
                <p v-if="word.gloss" class="text-xs text-gray-500 italic mt-2">
                  {{ word.gloss }}
                </p>
              </div>
            </div>
          </div>

          <!-- ── Summary table ── -->
          <details class="bg-white rounded-xl shadow-md p-6 group">
            <summary class="cursor-pointer text-emerald-700 hover:text-emerald-900
                           font-semibold text-lg transition-colors
                           flex items-center gap-2">
              <span class="group-open:rotate-90 transition-transform duration-200">▶</span>
              📋 Lihat Semua Detail
            </summary>
            <div class="mt-4 overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-amber-50 border-b-2 border-amber-200">
                    <th class="p-3 text-left text-amber-800">#</th>
                    <th class="p-3 text-right text-amber-800">Arab</th>
                    <th class="p-3 text-left text-amber-800">Lemma</th>
                    <th class="p-3 text-left text-amber-800">Akar</th>
                    <th class="p-3 text-left text-amber-800">Jenis</th>
                    <th class="p-3 text-left text-amber-800">Arti</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(word, i) in result.words"
                    :key="'t'+i"
                    class="border-b border-amber-100 hover:bg-amber-50 transition-colors"
                  >
                    <td class="p-3 text-gray-400">{{ i + 1 }}</td>
                    <td class="p-3 font-arabic text-right text-lg" dir="rtl">{{ word.word }}</td>
                    <td class="p-3 font-medium text-emerald-700">{{ word.lemma }}</td>
                    <td class="p-3 text-gray-400">{{ word.root !== '—' ? word.root : '—' }}</td>
                    <td class="p-3">
                      <span class="px-2 py-0.5 rounded-full text-xs font-bold" :class="posBadgeClass(word.pos_type)">
                        {{ word.pos_arabic }}
                      </span>
                    </td>
                    <td class="p-3 text-gray-600 italic">{{ word.gloss || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </Transition>
    </main>

    <footer class="text-center text-gray-400 text-sm py-6">
      Penerjemah Kitab — Dibangun langkah demi langkah
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
  gloss: string
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
