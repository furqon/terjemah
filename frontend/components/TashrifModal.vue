<template>
  <Teleport to="body">
    <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-start justify-center pt-10 pb-8 overflow-y-auto" style="background: rgba(0,0,0,0.5);" @click.self="$emit('close')">
        <div class="w-full max-w-3xl mx-4 rounded-lg overflow-hidden" style="background: #fffdf5; border: 1px solid #d4c5a9; box-shadow: 0 8px 32px rgba(0,0,0,0.2);">

          <!-- ═══ HEADER ═══ -->
          <div class="flex items-center justify-between px-4 py-3" style="background: linear-gradient(135deg, #1a3a2a, #2d5a3d);">
            <div class="flex items-center gap-2">
              <span style="font-size: 16px; color: #c9a84c;">📖</span>
              <span class="text-sm font-bold tracking-wider" style="color: #f5f0e8;">Tashrif Ishthilahi</span>
            </div>
            <button @click="$emit('close')" class="text-sm transition-colors" style="color: #a0896a;"
              @mouseenter="$event.target.style.color = '#c9a84c'" @mouseleave="$event.target.style.color = '#a0896a'">✕</button>
          </div>

          <!-- ═══ LOADING ═══ -->
          <div v-if="loading" class="p-8 text-center">
            <div class="inline-block animate-spin h-8 w-8 mb-3" style="border: 3px solid #e0d5c0; border-top-color: #c9a84c; border-radius: 50%;"></div>
            <p class="text-sm italic" style="color: #a0896a;">Menganalisis <strong>{{ root }}</strong>...</p>
          </div>

          <!-- ═══ ERROR ═══ -->
          <div v-if="error" class="p-6">
            <div class="px-4 py-3 rounded-lg" style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;">
              <p class="text-sm font-medium">Tashrif Tidak Tersedia</p>
              <p class="text-xs mt-1">{{ error }}</p>
            </div>
          </div>

          <!-- ═══ RESULT ═══ -->
          <div v-if="data" class="divide-y" style="border-color: #e0d5c0;">

            <!-- Root Info Banner -->
            <div class="p-4 text-center" style="background: #faf8f0;">
              <div class="flex items-center justify-center gap-3 flex-wrap">
                <span class="inline-block px-4 py-1.5 rounded-lg text-xl font-arabic transition-all duration-200 hover:scale-105"
                  style="background: #f0eadc; color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif; border: 1px solid #d4c5a9;">
                  {{ data.root }}
                </span>
                <span v-if="data.rumus" class="inline-block px-3 py-1 rounded-lg text-sm font-bold tracking-wider"
                  :style="rumusBadgeStyle(data.rumus)">
                  Rumus {{ data.rumus }}
                </span>
                <span v-if="data.bab" class="text-[11px]" style="color: #8b7355;">
                  Bab {{ data.bab }}
                </span>
              </div>
              <p class="text-[11px] mt-1.5 tracking-wider" style="color: #8b7355;">{{ data.classification }}</p>

              <div v-if="data.root_meaning?.id || data.rumus_semantic?.id" class="flex items-center justify-center gap-4 mt-2 text-xs flex-wrap">
                <span v-if="data.root_meaning?.id" class="px-2 py-0.5 rounded" style="background: #f0fdf4; color: #166534;">
                  {{ '✦' }} Akar: {{ data.root_meaning.id }} / {{ data.root_meaning.en }}
                </span>
                <span v-if="data.rumus_semantic?.id" class="px-2 py-0.5 rounded" style="background: #fefce8; color: #854d0e;">
                  {{ '◈' }} {{ data.rumus_semantic.id }}
                </span>
                <span v-if="data.verb_base?.id" class="px-2 py-0.5 rounded" style="background: #eff6ff; color: #1e40af;">
                  {{ '►' }} Dasar: {{ data.verb_base.id }}
                </span>
              </div>
            </div>

            <!-- ═══ 8-COLUMN ISHTHILAHI GRID ═══ -->
            <div class="p-4">
              <div class="flex items-center gap-1.5 mb-3">
                <span class="text-xs font-bold tracking-wider" style="color: #8b7355;">8 KOLOM TASHRIF ISHTHILAHI</span>
                <span style="flex: 1; border-top: 1px solid #e0d5c0;"></span>
              </div>

              <!-- Row 1: Forms 4-1 (RTL order) -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2" dir="rtl">
                <div v-for="form in ishthilahiRow1" :key="'r1-'+form.form_number"
                  class="rounded-lg overflow-hidden transition-all duration-200 hover:shadow-md"
                  style="border: 1px solid #e0d5c0;">
                  <div class="px-2 py-1 text-center" style="background: #f0eadc; border-bottom: 1px solid #d4c5a9;">
                    <span class="text-[9px] font-bold tracking-wider" style="color: #5a4a2a;">{{ form.form_name.replace('_', ' ') }}</span>
                  </div>
                  <div class="p-2 text-center">
                    <p class="text-base font-arabic leading-relaxed" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ form.value || '—' }}</p>
                    <p class="text-[10px] mt-0.5 leading-tight" style="color: #3a7a4d;">{{ form.translation_id || '' }}</p>
                    <p v-if="form.translation_en" class="text-[8px]" style="color: #6a8aaa;">{{ form.translation_en }}</p>
                  </div>
                  <div v-if="form.source" class="text-center pb-1">
                    <span class="inline-block px-1.5 py-[1px] rounded text-[8px]" :style="sourceBadgeStyle(form.source)">{{ form.source }}</span>
                  </div>
                </div>
              </div>

              <!-- Row 2: Forms 8-5 (RTL order) -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2" dir="rtl">
                <div v-for="form in ishthilahiRow2" :key="'r2-'+form.form_number"
                  class="rounded-lg overflow-hidden transition-all duration-200 hover:shadow-md"
                  style="border: 1px solid #e0d5c0;">
                  <div class="px-2 py-1 text-center" style="background: #f0eadc; border-bottom: 1px solid #d4c5a9;">
                    <span class="text-[9px] font-bold tracking-wider" style="color: #5a4a2a;">{{ form.form_name.replace('_', ' ') }}</span>
                  </div>
                  <div class="p-2 text-center">
                    <p class="text-base font-arabic leading-relaxed" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ form.value || '—' }}</p>
                    <p class="text-[10px] mt-0.5 leading-tight" style="color: #3a7a4d;">{{ form.translation_id || '' }}</p>
                    <p v-if="form.translation_en" class="text-[8px]" style="color: #6a8aaa;">{{ form.translation_en }}</p>
                  </div>
                  <div v-if="form.source" class="text-center pb-1">
                    <span class="inline-block px-1.5 py-[1px] rounded text-[8px]" :style="sourceBadgeStyle(form.source)">{{ form.source }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- ═══ TASHRIF LUGHOWI ═══ -->
            <div class="p-4">
              <details class="group">
                <summary class="cursor-pointer text-xs font-medium tracking-wider flex items-center gap-1.5 px-1 py-1" style="color: #8b7355;">
                  <span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="color: #c9a84c;">▸</span>
                  <span class="font-bold">Tashrif Lughowi</span>
                  <span class="text-[9px] font-normal" style="color: #a0896a;">(Konjugasi 13 Pronoun)</span>
                </summary>

                <div class="mt-3 space-y-4">
                  <!-- Past Tense -->
                  <div v-if="hasLughowi('past_tense')">
                    <div class="flex items-center gap-1.5 mb-1.5">
                      <span class="text-[10px] font-bold tracking-wider" style="color: #8b7355;">الفعل الماضي — Fi'il Madhi (Past)</span>
                      <span style="flex: 1; border-top: 1px dashed #e0d5c0;"></span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                      <div v-for="row in data.lughowi.past_tense" :key="'past-'+row.pronoun"
                        class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                        <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                        <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Present Tense -->
                  <div v-if="hasLughowi('present_tense')">
                    <div style="border-top: 1px solid #e0d5c0;" class="pt-3"></div>
                    <div class="flex items-center gap-1.5 mb-1.5">
                      <span class="text-[10px] font-bold tracking-wider" style="color: #8b7355;">الفعل المضارع — Fi'il Mudhari' (Present)</span>
                      <span style="flex: 1; border-top: 1px dashed #e0d5c0;"></span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                      <div v-for="row in data.lughowi.present_tense" :key="'pres-'+row.pronoun"
                        class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                        <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                        <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Subjunctive (collapsible) -->
                  <div v-if="hasLughowi('present_subjunctive')">
                    <details class="group">
                      <summary class="cursor-pointer text-[10px] font-medium tracking-wider flex items-center gap-1.5 px-1 py-1" style="color: #a0896a;">
                        <span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="color: #c9a84c;">▸</span>
                        المضارع منصوب — Present Subjunctive
                      </summary>
                      <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5 mt-2">
                        <div v-for="row in data.lughowi.present_subjunctive" :key="'subj-'+row.pronoun"
                          class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                          <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                          <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text }}</span>
                        </div>
                      </div>
                    </details>
                  </div>

                  <!-- Jussive (collapsible) -->
                  <div v-if="hasLughowi('present_jussive')">
                    <details class="group">
                      <summary class="cursor-pointer text-[10px] font-medium tracking-wider flex items-center gap-1.5 px-1 py-1" style="color: #a0896a;">
                        <span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="color: #c9a84c;">▸</span>
                        المضارع مجزوم — Present Jussive
                      </summary>
                      <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5 mt-2">
                        <div v-for="row in data.lughowi.present_jussive" :key="'jus-'+row.pronoun"
                          class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                          <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                          <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text }}</span>
                        </div>
                      </div>
                    </details>
                  </div>

                  <!-- Imperative -->
                  <div v-if="hasLughowi('imperative')">
                    <div style="border-top: 1px solid #e0d5c0;" class="pt-3"></div>
                    <div class="flex items-center gap-1.5 mb-1.5">
                      <span class="text-[10px] font-bold tracking-wider" style="color: #8b7355;">فعل الأمر — Fi'il Amr (Imperative)</span>
                      <span style="flex: 1; border-top: 1px dashed #e0d5c0;"></span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                      <div v-for="row in data.lughowi.imperative" :key="'amr-'+row.pronoun"
                        class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                        <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                        <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text || '—' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Nahi -->
                  <div v-if="hasLughowi('nahi')">
                    <div style="border-top: 1px solid #e0d5c0;" class="pt-3"></div>
                    <div class="flex items-center gap-1.5 mb-1.5">
                      <span class="text-[10px] font-bold tracking-wider" style="color: #8b7355;">فعل النهي — Fi'il Nahi (Prohibition)</span>
                      <span style="flex: 1; border-top: 1px dashed #e0d5c0;"></span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                      <div v-for="row in data.lughowi.nahi" :key="'nahi-'+row.pronoun"
                        class="flex items-center gap-2 px-2.5 py-1.5 rounded" style="background: #faf8f0; border: 1px solid #e8dcc8;">
                        <span class="text-[10px] font-medium flex-shrink-0" style="color: #a0896a; min-width: 36px;">{{ row.pronoun }}</span>
                        <span class="text-sm font-arabic" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ row.text || '—' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </details>
            </div>

            <!-- ═══ FOOTER ═══ -->
            <div class="px-4 py-3 flex items-center justify-between" style="background: #faf8f0;">
              <span v-if="data.rumus" class="text-[9px] tracking-wider" style="color: #a0896a;">
                {{ '⏺' }} Keyakinan: {{ (data.confidence * 100).toFixed(0) }}%
              </span>
              <span class="text-[9px]" style="color: #c9a84c;">
                {{ data.ishthilahi_table.length }} bentuk
              </span>
            </div>

          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

/* ── Props & Emits ── */
const props = defineProps<{
  visible: boolean
  root: string
  word?: string
}>()

const emit = defineEmits<{
  close: []
}>()

/* ── Types ── */
interface TashrifRow {
  form_number: number
  form_name: string
  form_label_ar: string
  form_label_id: string
  value: string
  source: string
  translation_id: string
  translation_en: string
}

interface TashrifLughowiRow {
  pronoun: string
  text: string
  description: string
}

interface TashrifResponse {
  root: string
  rumus: string
  bab: number
  classification: string
  meaning_pattern: string
  confidence: number
  root_meaning: { id: string; en: string }
  rumus_semantic: { id: string; en: string }
  verb_base: { id: string; en: string }
  ishthilahi_table: TashrifRow[]
  lughowi: Record<string, TashrifLughowiRow[]>
  current_form: Record<string, unknown>
}

/* ── State ── */
const data = ref<TashrifResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const config = useRuntimeConfig()

/* ── Computed: Split table into 2 rows of 4 ── */
/* ── Computed: Split table into 2 rows of 4 (RTL order) ── */
const ishthilahiRow1 = computed(() => {
  if (!data.value?.ishthilahi_table) return []
  return data.value.ishthilahi_table.filter(f => f.form_number >= 1 && f.form_number <= 4)
})
const ishthilahiRow2 = computed(() => {
  if (!data.value?.ishthilahi_table) return []
  return data.value.ishthilahi_table.filter(f => f.form_number >= 5 && f.form_number <= 8)
})

/* ── Helpers ── */
function hasLughowi(key: string): boolean {
  return !!(data.value?.lughowi?.[key] && data.value.lughowi[key].length > 0 &&
    data.value.lughowi[key].some(r => r.text))
}

function rumusBadgeStyle(rumus: string): Record<string, string> {
  const colors: Record<string, string[]> = {
    '3A': ['#f0fdf4', '#166534'],
    '3B': ['#eff6ff', '#1e40af'],
    '3C': ['#fefce8', '#854d0e'],
    '4A': ['#fdf2f8', '#9d174d'],
    '4B': ['#f5f3ff', '#5b21b6'],
    '4C': ['#fff7ed', '#9a3412'],
    '4D': ['#f0fdfa', '#115e59'],
    '5A': ['#fef2f2', '#991b1b'],
    '5B': ['#f0f9ff', '#075985'],
    '5C': ['#faf5ff', '#6d28d9'],
    '5D': ['#fefce8', '#854d0e'],
    '5E': ['#fff1f2', '#9f1239'],
    '6':  ['#f0fdf4', '#166534'],
  }
  const c = colors[rumus] || ['#f0eadc', '#8b7355']
  return { background: c[0], color: c[1], border: `1px solid ${c[0]}` }
}

function sourceBadgeStyle(source: string): Record<string, string> {
  if (source === 'sarf') return { background: '#fef3c7', color: '#92400e' }
  if (source === 'pattern') return { background: '#e0e7ff', color: '#3730a3' }
  return { background: '#f3f4f6', color: '#4b5563' }
}

/* ── Fetch data when visible ── */
watch(() => props.visible, async (isVisible) => {
  if (!isVisible || !props.root) return

  loading.value = true
  error.value = null
  data.value = null

  try {
    const res = await fetch(`${config.public.apiBase}/api/tashrif/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ root: props.root, word: props.word || '' })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Error: ${res.status}` }))
      throw new Error(err.detail || `Error: ${res.status}`)
    }
    data.value = await res.json()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Gagal menganalisis tashrif'
  } finally {
    loading.value = false
  }
})
</script>
