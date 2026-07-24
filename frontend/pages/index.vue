<template>
  <div class="min-h-screen" style="background: #f5f0e8">
    <!-- ── Traditional header ── -->
    <header class="relative overflow-hidden" style="background: linear-gradient(135deg, #1a3a2a 0%, #2d5a3d 50%, #1a3a2a 100%)">
      <!-- Ornamental top border -->
      <div class="h-2" style="background: repeating-linear-gradient(90deg, #c9a84c 0px, #c9a84c 4px, #1a3a2a 4px, #1a3a2a 6px, #c9a84c 6px, #c9a84c 10px, #1a3a2a 10px, #1a3a2a 12px);"></div>
      
      <!-- Decorative band -->
      <div class="h-1" style="background: linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%); opacity: 0.5;"></div>

      <div class="max-w-4xl mx-auto px-4 py-5 text-center relative">
        <!-- Decorative corner ornaments -->
        <div class="absolute left-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="color: #c9a84c">﴿</div>
        <div class="absolute right-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="color: #c9a84c">﴾</div>

        <h1 class="text-2xl font-bold tracking-wide" style="font-family: 'Amiri', 'Traditional Arabic', serif; color: #f5f0e8;">
          Penerjemah Kitab
        </h1>
        <p class="text-xs mt-1 tracking-wider" style="color: #c9a84c;">
          ✦ Analisis Kata Per Kata ✦
        </p>
      </div>

      <!-- Decorative bottom band -->
      <div class="h-1" style="background: linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%); opacity: 0.5;"></div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-4">
      <!-- ── Input section ── -->
      <div class="mb-3 rounded-lg" style="background: #fffdf5; border: 1px solid #e8dcc8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div class="p-3">
          <label class="block text-xs font-medium mb-1 tracking-wider" style="color: #8b7355;">
            Tulis Teks Arab
          </label>
          <textarea
            v-model="inputText"
            placeholder="يكتب الطالب الدرس في المكتبة..."
            class="w-full h-24 p-3 rounded-lg text-base font-arabic transition-colors resize-y"
            style="background: #faf8f0; border: 1px solid #e0d5c0; color: #3a2a1a;"
            dir="rtl"
            @focus="$event.target.style.borderColor = '#c9a84c'"
            @blur="$event.target.style.borderColor = '#e0d5c0'"
          ></textarea>

          <button
            @click="analyze"
            :disabled="loading || !inputText.trim()"
            class="mt-2 w-full font-medium py-2 px-4 rounded-lg text-sm tracking-wider transition-all duration-200 disabled:cursor-not-allowed"
            style="background: linear-gradient(135deg, #2d5a3d, #1a3a2a); color: #f5f0e8;"
            :style="loading || !inputText.trim() ? { opacity: 0.5 } : {}"
            @mouseenter="($event) => { if (!loading && inputText.trim()) { $event.target.style.background = 'linear-gradient(135deg, #3a7a4d, #2d5a3d)' } }"
            @mouseleave="($event) => { $event.target.style.background = 'linear-gradient(135deg, #2d5a3d, #1a3a2a)' }"
          >
            <span v-if="loading" class="flex items-center justify-center gap-1.5">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Memproses...
            </span>
            <span v-else>{{ '☾' }} Analisis Teks</span>
          </button>
        </div>
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
          class="px-3 py-2 rounded-lg mb-3 text-sm"
          style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;"
        >
          {{ error }}
        </div>
      </Transition>

      <!-- Result -->
      <Transition
        enter-active-class="transition duration-400 ease-out"
        enter-from-class="opacity-0 translate-y-4"
      >
        <div v-if="result" class="space-y-3">
          <!-- ══════ KITAB PAGE ══════ -->
          <div class="relative overflow-hidden rounded-lg" style="background: #fffdf5; border: 1px solid #d4c5a9; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <!-- Outer ornamental border -->
            <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%);"></div>

            <!-- Page header -->
            <div class="text-center pt-4 pb-2 px-4">
              <div class="text-xs tracking-widest" style="color: #8b7355;">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>
              <div class="mt-1" style="border-top: 1px solid #e8dcc8; width: 60px; margin-left: auto; margin-right: auto;"></div>
              <div class="mt-2 flex items-center justify-center gap-2 text-xs" style="color: #a0896a;">
                <span>▸</span>
                <span class="tracking-wider">Teks Arab</span>
                <span>◂</span>
              </div>
            </div>

            <!-- Arabic text in a decorative frame -->
            <div class="mx-4 p-4 text-center rounded" style="background: #faf8f0; border: 1px solid #e0d5c0;">
              <div class="flex flex-wrap justify-center gap-x-4 gap-y-1" dir="rtl">
                <span
                  v-for="(word, i) in result.words"
                  :key="'ar-'+i"
                  class="text-3xl md:text-4xl font-arabic leading-relaxed transition-all duration-200 hover:scale-105 hover:text-[#c9a84c] cursor-default"
                  style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif; text-shadow: 0 1px 1px rgba(0,0,0,0.05);"
                  :title="word.gloss_id"
                >
                  {{ word.word }}
                  <span v-if="i < result.words.length - 1" class="text-lg opacity-30 select-none" style="color: #a0896a;"> </span>
                </span>
              </div>
            </div>              <!-- Ornamental divider -->
            <div class="flex items-center justify-center gap-2 px-4 py-3" style="color: #c9a84c;">
              <span style="border-top: 1px solid; flex: 1; max-width: 60px; opacity: 0.5;"></span>
              <span style="font-size: 16px; line-height: 1;">◈</span>
              <span style="border-top: 1px solid; flex: 1; max-width: 60px; opacity: 0.5;"></span>
            </div>

            <!-- Copy button -->
            <div class="text-center px-4 pb-2">
              <button
                @click="copyResult"
                class="text-[10px] tracking-wider py-1 px-3 rounded transition-all duration-200"
                style="color: #8b7355; border: 1px solid #e0d5c0; background: #faf8f0;"
                @mouseenter="$event.target.style.background = '#f5f0e0'"
                @mouseleave="$event.target.style.background = '#faf8f0'"
              >
                Salin Teks
              </button>
            </div>

            <!-- Section label -->
            <div class="px-4 pb-1">
              <div class="flex items-center justify-center gap-2 text-xs" style="color: #a0896a;">
                <span>▸</span>
                <span class="tracking-wider">Analisis Per Kata</span>
                <span>◂</span>
              </div>
            </div>

            <!-- Word columns - Scholar style -->
            <div class="px-4 pb-4">
              <div class="flex flex-wrap justify-center gap-1" style="direction: rtl;">
                <div
                  v-for="(word, i) in result.words"
                  :key="i"
                  class="word-card flex flex-col items-center rounded-sm transition-all duration-300"
                  style="direction: ltr; min-width: 90px; max-width: 130px; flex: 1 0 auto;"
                >
                  <!-- Vertical analysis stack -->
                  <div class="w-full text-center px-1.5 py-1.5" style="background: #faf8f0;">
                    <!-- Arabic word (main) -->
                    <p class="text-xl font-arabic leading-tight transition-colors duration-200" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">
                      {{ word.word }}
                    </p>

                    <!-- Lemma -->
                    <p class="text-[11px] font-medium mt-0.5" style="color: #5a7a4a;">
                      {{ word.lemma }}
                    </p>

                    <!-- Root (very small) -->
                    <p v-if="word.root && word.root !== '—'" class="text-[9px]" style="color: #a0896a;">
                      ({{ word.root }})
                    </p>

                    <!-- POS badge -->
                    <span
                      class="inline-block mt-[2px] px-1.5 py-[1px] rounded-sm text-[9px] font-bold"
                      :class="posBadgeClass(word.pos_type)"
                    >
                      {{ word.pos_arabic }}
                    </span>

                    <!-- Translations -->
                    <div class="mt-1 leading-tight">
                      <p v-if="word.gloss_id" class="text-[10px] font-medium" style="color: #3a7a4d;" title="Indonesian">
                        {{ word.gloss_id }}
                      </p>
                      <p v-if="word.gloss_en" class="text-[9px]" style="color: #6a8aaa;" title="English">
                        {{ word.gloss_en }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Page footer - word count -->
            <div class="text-center pb-3">
              <div style="border-top: 1px solid #e8dcc8; width: 40%; margin-left: auto; margin-right: auto;"></div>
              <p class="text-[10px] mt-2 tracking-wider" style="color: #a0896a;">
                {{ result.word_count }} kata — {{ result.original.length }} karakter
              </p>
            </div>

            <!-- Bottom ornamental border -->
            <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%);"></div>
          </div>

          <!-- ══════ TRANSLATIONS ══════ -->
          <!-- Loading indicator -->
          <div
            v-if="translating"
            class="rounded-lg p-4 text-center"
            style="background: #fffdf5; border: 1px solid #d4c5a9;"
          >
            <p class="text-sm italic" style="color: #a0896a;">Menerjemahkan...</p>
          </div>

          <!-- Translation results -->
          <div
            v-if="translation"
            class="rounded-lg overflow-hidden"
            style="background: #fffdf5; border: 1px solid #d4c5a9;"
          >
            <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #3a7a4d 30%, #3a7a4d 70%, #d4c5a9 100%);"></div>
            
            <div class="p-4">
              <div class="flex items-center justify-center gap-2 text-xs mb-3" style="color: #a0896a;">
                <span>▸</span>
                <span class="tracking-wider">Terjemahan Lengkap</span>
                <span>◂</span>
              </div>

              <div class="space-y-3">
                <!-- Arabic text -->
                <div class="text-right" dir="rtl">
                  <p class="text-[10px] tracking-wider mb-1" style="color: #8b7355;">TEKS ARAB</p>
                  <p class="text-xl font-arabic leading-relaxed" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">
                    {{ result.harakat }}
                  </p>
                </div>

                <div style="border-top: 1px dashed #e0d5c0;"></div>

                <!-- Indonesian -->
                <div>
                  <p class="text-[10px] tracking-wider mb-1" style="color: #3a7a4d;">BAHASA INDONESIA</p>
                  <p class="text-base leading-relaxed" style="color: #2a4a3a;">
                    {{ translation.translation_id }}
                  </p>
                </div>

                <div style="border-top: 1px dashed #e0d5c0;"></div>

                <!-- English -->
                <div>
                  <p class="text-[10px] tracking-wider mb-1" style="color: #4a6a8a;">ENGLISH</p>
                  <p class="text-base leading-relaxed" style="color: #2a3a4a;">
                    {{ translation.translation_en }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- ══════ DETAIL TABLE ══════ -->
          <details class="group rounded-lg overflow-hidden" style="background: #fffdf5; border: 1px solid #d4c5a9;">
            <summary class="cursor-pointer px-4 py-2.5 text-xs tracking-wider font-medium flex items-center justify-between transition-colors" style="color: #5a7a4a;">
              <span class="flex items-center gap-1.5">
                <span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="color: #c9a84c;">▸</span>
                Detail Lengkap
              </span>
              <span style="color: #a0896a;">{{ result.word_count }} kata</span>
            </summary>
            <div class="px-4 pb-3 overflow-x-auto">
              <table class="w-full text-xs border-collapse">
                <thead>
                  <tr style="border-bottom: 1px solid #e0d5c0;">
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">#</th>
                    <th class="p-2 text-right font-medium" style="color: #8b7355;">Arab</th>
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">Lemma</th>
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">Akar</th>
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">Jenis</th>
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">ID</th>
                    <th class="p-2 text-left font-medium" style="color: #8b7355;">EN</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(word, i) in result.words"
                    :key="'t'+i"
                    class="transition-colors"
                    style="border-bottom: 1px solid #f0eadc;"
                    @mouseenter="$event.currentTarget.style.background = '#faf8f0'"
                    @mouseleave="$event.currentTarget.style.background = 'transparent'"
                  >
                    <td class="p-2" style="color: #a0896a;">{{ i + 1 }}</td>
                    <td class="p-2 font-arabic text-right text-sm" dir="rtl" style="color: #3a2a1a;">{{ word.word }}</td>
                    <td class="p-2 font-medium" style="color: #5a7a4a;">{{ word.lemma }}</td>
                    <td class="p-2" style="color: #a0896a;">{{ word.root !== '—' ? word.root : '—' }}</td>
                    <td class="p-2">
                      <span class="px-1.5 py-0.5 rounded-sm text-[10px] font-bold" :class="posBadgeClass(word.pos_type)">
                        {{ word.pos_arabic }}
                      </span>
                    </td>
                    <td class="p-2" style="color: #3a7a4d;">{{ word.gloss_id || '—' }}</td>
                    <td class="p-2" style="color: #5a7a8a;">{{ word.gloss_en || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </Transition>
    </main>

    <footer class="text-center py-4">
      <div class="max-w-4xl mx-auto px-4">
        <div class="flex items-center justify-center gap-2 text-[10px] tracking-wider" style="color: #a0896a;">
          <span style="border-top: 1px solid #d4c5a9; flex: 1; max-width: 40px;"></span>
          <span>Penerjemah Kitab</span>
          <span style="border-top: 1px solid #d4c5a9; flex: 1; max-width: 40px;"></span>
        </div>
      </div>
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
  noun: 'noun-badge',
  verb: 'verb-badge',
  prep: 'prep-badge',
  conj: 'prep-badge',
  part: 'part-badge',
  pron: 'pron-badge',
  adj: 'adj-badge',
  adv: 'adv-badge',
  det: 'det-badge',
  dem: 'dem-badge',
  neg: 'neg-badge',
  interr: 'interr-badge',
  num: 'num-badge',
  noun_num: 'num-badge',
  noun_quant: 'num-badge',
  rel: 'rel-badge',
  noun_prop: 'noun-badge',
  abbrev: 'part-badge',
}

function posBadgeClass(type: string): string {
  return posColors[type] || 'default-badge'
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
      console.warn('Translation error:', err.detail)
      return
    }
    const data = await res.json()
    if (requestId !== _translateId) return
    translation.value = { translation_id: data.translation_id, translation_en: data.translation_en }
  } catch (e) {
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
  font-family: 'Amiri', 'Traditional Arabic', serif !important;
}

/* ── Traditional kitab styling ── */

/* POS badge colors */
.noun-badge {
  background: #dcfce7;
  color: #166534;
}
.verb-badge {
  background: #ffedd5;
  color: #9a3412;
}
.prep-badge {
  background: #f3e8ff;
  color: #6b21a8;
}
.part-badge {
  background: #f3f4f6;
  color: #4b5563;
}
.pron-badge {
  background: #fce7f3;
  color: #9d174d;
}
.adj-badge {
  background: #d1fae5;
  color: #065f46;
}
.adv-badge {
  background: #ccfbf1;
  color: #115e59;
}
.det-badge {
  background: #e0e7ff;
  color: #3730a3;
}
.dem-badge {
  background: #fce7f3;
  color: #9d174d;
}
.neg-badge {
  background: #fee2e2;
  color: #991b1b;
}
.interr-badge {
  background: #cffafe;
  color: #155e75;
}
.num-badge {
  background: #ecfccb;
  color: #3f6212;
}
.rel-badge {
  background: #f3e8ff;
  color: #6b21a8;
}
.default-badge {
  background: #f3f4f6;
  color: #4b5563;
}

/* Word card hover animation */
.word-card {
  transition: all 0.3s ease;
}
.word-card:hover {
  transform: translateY(-2px);
  z-index: 10;
}
.word-card:hover > div {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-radius: 4px;
}

/* Staggered card animation on mount */
.word-card {
  animation: kitabReveal 0.5s ease-out both;
}

@keyframes kitabReveal {
  from {
    opacity: 0;
    transform: translateY(10px);
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

/* POS badge hover states */
.noun-badge:hover { background: #bbf7d0; }
.verb-badge:hover { background: #fed7aa; }
.prep-badge:hover { background: #e9d5ff; }
.part-badge:hover { background: #e5e7eb; }
.pron-badge:hover { background: #fbcfe8; }
.adj-badge:hover { background: #a7f3d0; }
.adv-badge:hover { background: #99f6e4; }
.det-badge:hover { background: #c7d2fe; }
.dem-badge:hover { background: #fbcfe8; }
.neg-badge:hover { background: #fecaca; }
.interr-badge:hover { background: #a5f3fc; }
.num-badge:hover { background: #d9f99d; }
.rel-badge:hover { background: #e9d5ff; }
.default-badge:hover { background: #e5e7eb; }
</style>
