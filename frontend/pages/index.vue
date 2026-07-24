<template>
  <div class="min-h-screen" style="background: #f5f0e8">
    <!-- ── Header ── -->
    <header class="relative overflow-hidden" style="background: linear-gradient(135deg, #1a3a2a 0%, #2d5a3d 50%, #1a3a2a 100%)">
      <div class="h-2" style="background: repeating-linear-gradient(90deg, #c9a84c 0px, #c9a84c 4px, #1a3a2a 4px, #1a3a2a 6px, #c9a84c 6px, #c9a84c 10px, #1a3a2a 10px, #1a3a2a 12px);"></div>
      <div class="h-1" style="background: linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%); opacity: 0.5;"></div>
      <div class="max-w-4xl mx-auto px-4 py-5 text-center relative">
        <div class="absolute left-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="color: #c9a84c">﴿</div>
        <div class="absolute right-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="color: #c9a84c">﴾</div>
        <h1 class="text-2xl font-bold tracking-wide" style="font-family: 'Amiri', 'Traditional Arabic', serif; color: #f5f0e8;">Penerjemah Kitab</h1>
        <p class="text-xs mt-1 tracking-wider" style="color: #c9a84c;">✦ Analisis + OCR + Terjemahan ✦</p>
      </div>
      <div class="h-1" style="background: linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%); opacity: 0.5;"></div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-4">
      <!-- ── Tab Navigation ── -->
      <div class="flex gap-0 border-b mb-4" style="border-color: #d4c5a9;">
        <button @click="activeTab = 'analyze'" class="px-5 py-2.5 text-sm font-medium rounded-t-lg transition-all"
          :style="activeTab === 'analyze' ? { background: '#fffdf5', color: '#2d5a3d', border: '1px solid #d4c5a9', borderBottom: '1px solid #fffdf5', marginBottom: '-1px' } : { color: '#a0896a', border: '1px solid transparent' }"
        ><span class="flex items-center gap-1.5"><span>📖</span> Analisis Teks</span></button>
        <button @click="activeTab = 'scan'" class="px-5 py-2.5 text-sm font-medium rounded-t-lg transition-all"
          :style="activeTab === 'scan' ? { background: '#fffdf5', color: '#2d5a3d', border: '1px solid #d4c5a9', borderBottom: '1px solid #fffdf5', marginBottom: '-1px' } : { color: '#a0896a', border: '1px solid transparent' }"
        ><span class="flex items-center gap-1.5"><span>📄</span> Scan PDF</span></button>
      </div>

      <!-- ════════════ TAB 1: ANALISIS TEKS ════════════ -->
      <div v-if="activeTab === 'analyze'">
        <div class="mb-3 rounded-lg" style="background: #fffdf5; border: 1px solid #e8dcc8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <div class="p-3">
            <label class="block text-xs font-medium mb-1 tracking-wider" style="color: #8b7355;">Tulis Teks Arab</label>
            <textarea v-model="inputText" placeholder="يكتب الطالب الدرس في المكتبة..." dir="rtl"
              class="w-full h-24 p-3 rounded-lg text-base font-arabic transition-colors resize-y"
              style="background: #faf8f0; border: 1px solid #e0d5c0; color: #3a2a1a;"
              @focus="$event.target.style.borderColor = '#c9a84c'" @blur="$event.target.style.borderColor = '#e0d5c0'"></textarea>
            <button @click="analyze" :disabled="loading || !inputText.trim()"
              class="mt-2 w-full font-medium py-2 px-4 rounded-lg text-sm tracking-wider transition-all duration-200 disabled:cursor-not-allowed"
              style="background: linear-gradient(135deg, #2d5a3d, #1a3a2a); color: #f5f0e8;"
              :style="loading || !inputText.trim() ? { opacity: 0.5 } : {}"
              @mouseenter="($event) => { if (!loading && inputText.trim()) $event.target.style.background = 'linear-gradient(135deg, #3a7a4d, #2d5a3d)' }"
              @mouseleave="($event) => { $event.target.style.background = 'linear-gradient(135deg, #2d5a3d, #1a3a2a)' }"
            ><span v-if="loading" class="flex items-center justify-center gap-1.5"><svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Memproses...</span><span v-else>{{ '☾' }} Analisis Teks</span></button>
          </div>
        </div>

        <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0 -translate-y-2">
          <div v-if="error" class="px-3 py-2 rounded-lg mb-3 text-sm" style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;">{{ error }}</div>
        </Transition>

        <Transition enter-active-class="transition duration-400 ease-out" enter-from-class="opacity-0 translate-y-4">
          <div v-if="result" class="space-y-3">
            <!-- Kitab page display -->
            <div class="relative overflow-hidden rounded-lg" style="background: #fffdf5; border: 1px solid #d4c5a9; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
              <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%);"></div>
              <div class="text-center pt-4 pb-2 px-4">
                <div class="text-xs tracking-widest" style="color: #8b7355;">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>
                <div class="mt-1" style="border-top: 1px solid #e8dcc8; width: 60px; margin: 0 auto;"></div>
                <div class="mt-2 flex items-center justify-center gap-2 text-xs" style="color: #a0896a;"><span>▸</span><span class="tracking-wider">Teks Arab</span><span>◂</span></div>
              </div>
              <div class="mx-4 p-4 text-center rounded" style="background: #faf8f0; border: 1px solid #e0d5c0;">
                <div class="flex flex-wrap justify-center gap-x-4 gap-y-1" dir="rtl">
                  <span v-for="(word, i) in result.words" :key="'ar-'+i"
                    class="text-3xl md:text-4xl font-arabic leading-relaxed transition-all duration-200 hover:scale-105 hover:text-[#c9a84c] cursor-default"
                    style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif; text-shadow: 0 1px 1px rgba(0,0,0,0.05);" :title="word.gloss_id"
                  >{{ word.word }}<span v-if="i < result.words.length - 1" class="text-lg opacity-30 select-none" style="color: #a0896a;"> </span></span>
                </div>
              </div>
              <div class="flex items-center justify-center gap-2 px-4 py-3" style="color: #c9a84c;">
                <span style="border-top: 1px solid; flex: 1; max-width: 60px; opacity: 0.5;"></span>
                <span style="font-size: 16px; line-height: 1;">◈</span>
                <span style="border-top: 1px solid; flex: 1; max-width: 60px; opacity: 0.5;"></span>
              </div>
              <div class="text-center px-4 pb-2">
                <button @click="copyResult" class="text-[10px] tracking-wider py-1 px-3 rounded transition-all duration-200"
                  style="color: #8b7355; border: 1px solid #e0d5c0; background: #faf8f0;"
                  @mouseenter="$event.target.style.background = '#f5f0e0'" @mouseleave="$event.target.style.background = '#faf8f0'">Salin Teks</button>
              </div>
              <div class="px-4 pb-1">
                <div class="flex items-center justify-center gap-2 text-xs" style="color: #a0896a;"><span>▸</span><span class="tracking-wider">Analisis Per Kata</span><span>◂</span></div>
              </div>
              <div class="px-4 pb-4">
                <div class="flex flex-wrap justify-center gap-1" style="direction: rtl;">
                  <div v-for="(word, i) in result.words" :key="i" class="word-card flex flex-col items-center rounded-sm transition-all duration-300" style="direction: ltr; min-width: 90px; max-width: 130px; flex: 1 0 auto;">
                    <div class="w-full text-center px-1.5 py-1.5" style="background: #faf8f0;">
                      <p class="text-xl font-arabic leading-tight" dir="rtl" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ word.word }}</p>
                      <p class="text-[11px] font-medium mt-0.5" style="color: #5a7a4a;">{{ word.lemma }}</p>
                      <p v-if="word.root && word.root !== '—'" class="text-[9px]" style="color: #a0896a;">({{ word.root }})</p>
                      <span class="inline-block mt-[2px] px-1.5 py-[1px] rounded-sm text-[9px] font-bold" :class="posBadgeClass(word.pos_type)">{{ word.pos_arabic }}</span>
                      <div class="mt-1 leading-tight">
                        <p v-if="word.gloss_id" class="text-[10px] font-medium" style="color: #3a7a4d;" title="Indonesian">{{ word.gloss_id }}</p>
                        <p v-if="word.gloss_en" class="text-[9px]" style="color: #6a8aaa;" title="English">{{ word.gloss_en }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="text-center pb-3">
                <div style="border-top: 1px solid #e8dcc8; width: 40%; margin: 0 auto;"></div>
                <p class="text-[10px] mt-2 tracking-wider" style="color: #a0896a;">{{ result.word_count }} kata — {{ result.original.length }} karakter</p>
              </div>
              <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%);"></div>
            </div>

            <!-- Translation results -->
            <div v-if="translating" class="rounded-lg p-4 text-center" style="background: #fffdf5; border: 1px solid #d4c5a9;"><p class="text-sm italic" style="color: #a0896a;">Menerjemahkan...</p></div>
            <div v-if="translation" class="rounded-lg overflow-hidden" style="background: #fffdf5; border: 1px solid #d4c5a9;">
              <div class="h-1" style="background: linear-gradient(90deg, #d4c5a9 0%, #3a7a4d 30%, #3a7a4d 70%, #d4c5a9 100%);"></div>
              <div class="p-4">
                <div class="flex items-center justify-center gap-2 text-xs mb-3" style="color: #a0896a;"><span>▸</span><span class="tracking-wider">Terjemahan Lengkap</span><span>◂</span></div>
                <div class="space-y-3">
                  <div class="text-right" dir="rtl"><p class="text-[10px] tracking-wider mb-1" style="color: #8b7355;">TEKS ARAB</p><p class="text-xl font-arabic leading-relaxed" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ result.harakat }}</p></div>
                  <div style="border-top: 1px dashed #e0d5c0;"></div>
                  <div><p class="text-[10px] tracking-wider mb-1" style="color: #3a7a4d;">BAHASA INDONESIA</p><p class="text-base leading-relaxed" style="color: #2a4a3a;">{{ translation.translation_id }}</p></div>
                  <div style="border-top: 1px dashed #e0d5c0;"></div>
                  <div><p class="text-[10px] tracking-wider mb-1" style="color: #4a6a8a;">ENGLISH</p><p class="text-base leading-relaxed" style="color: #2a3a4a;">{{ translation.translation_en }}</p></div>
                </div>
              </div>
            </div>

            <!-- Detail table -->
            <details class="group rounded-lg overflow-hidden" style="background: #fffdf5; border: 1px solid #d4c5a9;">
              <summary class="cursor-pointer px-4 py-2.5 text-xs tracking-wider font-medium flex items-center justify-between transition-colors" style="color: #5a7a4a;">
                <span class="flex items-center gap-1.5"><span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="color: #c9a84c;">▸</span> Detail Lengkap</span>
                <span style="color: #a0896a;">{{ result.word_count }} kata</span>
              </summary>
              <div class="px-4 pb-3 overflow-x-auto">
                <table class="w-full text-xs border-collapse">
                  <thead><tr style="border-bottom: 1px solid #e0d5c0;"><th class="p-2 text-left font-medium" style="color: #8b7355;">#</th><th class="p-2 text-right font-medium" style="color: #8b7355;">Arab</th><th class="p-2 text-left font-medium" style="color: #8b7355;">Lemma</th><th class="p-2 text-left font-medium" style="color: #8b7355;">Akar</th><th class="p-2 text-left font-medium" style="color: #8b7355;">Jenis</th><th class="p-2 text-left font-medium" style="color: #8b7355;">ID</th><th class="p-2 text-left font-medium" style="color: #8b7355;">EN</th></tr></thead>
                  <tbody>
                    <tr v-for="(word, i) in result.words" :key="'t'+i" class="transition-colors" style="border-bottom: 1px solid #f0eadc;" @mouseenter="$event.currentTarget.style.background = '#faf8f0'" @mouseleave="$event.currentTarget.style.background = 'transparent'">
                      <td class="p-2" style="color: #a0896a;">{{ i + 1 }}</td>
                      <td class="p-2 font-arabic text-right text-sm" dir="rtl" style="color: #3a2a1a;">{{ word.word }}</td>
                      <td class="p-2 font-medium" style="color: #5a7a4a;">{{ word.lemma }}</td>
                      <td class="p-2" style="color: #a0896a;">{{ word.root !== '—' ? word.root : '—' }}</td>
                      <td class="p-2"><span class="px-1.5 py-0.5 rounded-sm text-[10px] font-bold" :class="posBadgeClass(word.pos_type)">{{ word.pos_arabic }}</span></td>
                      <td class="p-2" style="color: #3a7a4d;">{{ word.gloss_id || '—' }}</td>
                      <td class="p-2" style="color: #5a7a8a;">{{ word.gloss_en || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </div>
        </Transition>
      </div>

      <!-- ════════════ TAB 2: SCAN PDF ════════════ -->
      <div v-if="activeTab === 'scan'" class="space-y-4">
        <div class="px-3 py-2 rounded-lg text-xs flex items-center gap-2"
          :style="tesseractOk ? { background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' } : { background: '#fefce8', border: '1px solid #fef08a', color: '#854d0e' }"
        ><span>{{ tesseractOk ? '✓' : '⚠' }}</span><span><strong>Tesseract:</strong> {{ tesseractOk ? tesseractVersion : 'Belum terinstal' }}</span></div>

        <div class="rounded-lg" style="background: #fffdf5; border: 1px solid #e8dcc8; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <div class="p-4">
            <h2 class="text-sm font-bold mb-3" style="color: #3a2a1a;"><span>📁</span> Upload PDF</h2>
            <div class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors mb-3"
              :style="dragOver ? { borderColor: '#c9a84c', background: '#fdf8ec' } : { borderColor: '#e0d5c0', background: '#faf8f0' }"
              @dragover.prevent="dragOver = true" @dragleave="dragOver = false" @drop.prevent="handleDrop" @click="$refs.fileInput.click()"
            >
              <input ref="fileInput" type="file" accept=".pdf" class="hidden" @change="handleFileSelect" />
              <div class="text-3xl mb-2" style="color: #c9a84c;">📄</div>
              <p class="text-sm font-medium" style="color: #3a2a1a;">{{ selectedFile ? selectedFile.name : 'Klik atau seret PDF' }}</p>
              <p v-if="!selectedFile" class="text-xs mt-1" style="color: #a0896a;">Format PDF, maks 50MB</p>
              <p v-if="selectedFile && pdfInfo" class="text-xs mt-1" style="color: #5a7a4a;">{{ pdfInfo.total_pages }} halaman</p>
            </div>
            <div class="flex items-end gap-3">
              <div><label class="text-[10px] block mb-1 tracking-wider" style="color: #8b7355;">Dari</label>
                <input v-model.number="pageStart" type="number" min="1" class="w-16 p-2 border rounded text-sm text-center" style="border-color: #e0d5c0; background: #faf8f0; color: #3a2a1a;"></div>
              <div><label class="text-[10px] block mb-1 tracking-wider" style="color: #8b7355;">Sampai</label>
                <input v-model.number="pageEnd" type="number" min="1" class="w-16 p-2 border rounded text-sm text-center" style="border-color: #e0d5c0; background: #faf8f0; color: #3a2a1a;"></div>
              <button @click="uploadAndProcess" :disabled="ocrProcessing || !selectedFile || !tesseractOk"
                class="flex-1 py-2.5 rounded-lg text-sm font-medium tracking-wider transition-all disabled:cursor-not-allowed"
                style="background: linear-gradient(135deg, #2d5a3d, #1a3a2a); color: #f5f0e8;" :style="ocrProcessing || !selectedFile || !tesseractOk ? { opacity: 0.5 } : {}"
              ><span v-if="ocrProcessing" class="flex items-center justify-center gap-1.5"><svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> {{ uploadStatus }}</span><span v-else>{{ '☾' }} Proses OCR</span></button>
            </div>
            <div v-if="ocrProcessing" class="mt-3">
              <div class="flex justify-between text-xs mb-1" style="color: #8b7355;"><span>Hal {{ ocrCurrentPage }}/{{ ocrTotalPages }}</span><span>{{ Math.round(ocrProgress * 100) }}%</span></div>
              <div class="h-2 rounded-full overflow-hidden" style="background: #e0d5c0;"><div class="h-full rounded-full transition-all" style="background: linear-gradient(90deg, #c9a84c, #2d5a3d);" :style="{ width: (ocrProgress * 100) + '%' }"></div></div>
            </div>
          </div>
        </div>

        <div v-if="ocrError" class="px-3 py-2 rounded-lg text-sm" style="background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;">{{ ocrError }}</div>

        <!-- PDF list with accordion pages -->
        <div v-if="pdfList.length > 0" class="space-y-3">
          <div v-for="pdf in pdfList" :key="pdf.id" class="rounded-lg overflow-hidden" style="background: #fffdf5; border: 1px solid #d4c5a9;">
            <div class="px-4 py-3 flex items-center justify-between" style="background: #faf8f0; border-bottom: 1px solid #e8dcc8;">
              <div class="flex items-center gap-2">
                <span class="text-lg">📄</span>
                <div><h3 class="text-sm font-semibold" style="color: #3a2a1a;">{{ pdf.filename }}</h3>
                  <p class="text-[10px]" style="color: #a0896a;">{{ pdf.total_pages }} hal • {{ pdf.pages_processed }} diproses • {{ pdf.pages_translated }} terjemah</p></div>
              </div>
              <div class="flex gap-1.5">
                <button v-if="pdf.pages_processed > 0 && pdf.pages_translated < pdf.pages_processed" @click="translatePdf(pdf.id)" :disabled="translatingPdfId === pdf.id"
                  class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50" style="background: #c9a84c; color: white;">
                  {{ translatingPdfId === pdf.id ? '...' : 'Terjemah Semua' }}</button>
                <button @click="deletePdf(pdf.id)" class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all"
                  style="background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;">Hapus</button>
              </div>
            </div>
            <div class="px-4 pb-3">
              <!-- Accordion page card -->
              <div v-for="page in getPages(pdf.id)" :key="page.id" class="mt-2 rounded-lg overflow-hidden" style="border: 1px solid #e0d5c0;">
                <!-- Clickable header -->
                <div @click="toggleExpand(page.id)"
                  class="flex items-center justify-between px-3 py-2 cursor-pointer select-none transition-colors"
                  style="background: #faf8f0;"
                  @mouseenter="$event.currentTarget.style.background = '#f5f0e0'" @mouseleave="$event.currentTarget.style.background = '#faf8f0'"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-xs inline-block transition-transform duration-200" :style="{ transform: expandedPages[page.id] ? 'rotate(90deg)' : 'rotate(0deg)' }" style="color: #a0896a;">▸</span>
                    <span class="text-xs font-medium" style="color: #8b7355;">Halaman {{ page.page_number }}</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span v-if="pageEdits[page.id] !== undefined && !editingPages[page.id]" class="text-[9px]" style="color: #c9a84c;">✎</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded" :style="page.confidence >= 0.8 ? { background: '#dcfce7', color: '#166534' } : page.confidence >= 0.5 ? { background: '#fef9c3', color: '#854d0e' } : { background: '#fee2e2', color: '#991b1b' }">
                      {{ Math.round(page.confidence * 100) }}%</span>
                    <span v-if="page.translated_id" class="text-[9px]" style="color: #3a7a4d;">✓</span>
                  </div>
                </div>

                <!-- Expandable content -->
                <div v-if="expandedPages[page.id]" class="px-3 py-3" style="background: #fffdf5; border-top: 1px solid #e0d5c0;">
                  <!-- VIEW MODE -->
                  <div v-if="!editingPages[page.id]">
                    <div class="mb-2" dir="rtl">
                      <p class="text-[10px] tracking-wider mb-1" style="color: #8b7355;">TEKS ARAB</p>
                      <p class="text-base font-arabic leading-relaxed" style="color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif;">{{ getPageText(page) }}</p>
                    </div>
                    <div class="flex justify-end gap-1.5">
                      <button @click="toggleEdit(page.id, true)" class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all flex items-center gap-1" style="background: #e0d5c0; color: #3a2a1a;">✎ Edit</button>
                      <button @click="translatePage(page.id, page.page_number, getEditedText(page))" :disabled="translatingPageId === page.id"
                        class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1"
                        style="background: #c9a84c; color: white;"
                      ><span v-if="translatingPageId === page.id"><svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></span><span v-else>{{ '☾' }} Terjemah</span></button>
                    </div>
                  </div>
                  <!-- EDIT MODE -->
                  <div v-else>
                    <div class="mb-2">
                      <div class="flex items-center justify-between mb-1">
                        <p class="text-[10px] tracking-wider" style="color: #8b7355;">EDIT TEKS ARAB</p>
                        <span class="text-[9px]" style="color: #a0896a;">{{ getEditLength(page) }} karakter</span>
                      </div>
                      <textarea :value="getPageText(page)" @input="updatePageEdit(page.id, ($event.target as HTMLTextAreaElement).value)" dir="rtl"
                        class="w-full p-2.5 rounded-lg text-base font-arabic leading-relaxed resize-y transition-colors"
                        style="background: #fffdf5; border: 1px solid #c9a84c; color: #3a2a1a; font-family: 'Amiri', 'Traditional Arabic', serif; min-height: 80px;"></textarea>
                    </div>
                    <div class="flex justify-end gap-1.5 flex-wrap">
                      <button @click="savePageText(page)" :disabled="savingPageIds[page.id]"
                        class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1"
                        style="background: #2d5a3d; color: white;">{{ savingPageIds[page.id] ? 'Menyimpan...' : '💾 Save' }}</button>
                      <button @click="tashkeelPageText(page)" :disabled="tashkeelingPageIds[page.id]"
                        class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1"
                        style="background: #6b21a8; color: white;">{{ tashkeelingPageIds[page.id] ? 'Tashkeel...' : '◌ Tashkeel' }}</button>
                      <button @click="translatePage(page.id, page.page_number, getEditedText(page))" :disabled="translatingPageId === page.id"
                        class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1"
                        style="background: #c9a84c; color: white;"
                      ><span v-if="translatingPageId === page.id"><svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></span><span v-else>{{ '☾' }} Terjemah</span></button>
                    </div>
                  </div>
                  <!-- Translation results inside accordion -->
                  <div v-if="page.translated_id" class="pt-2 mt-2" style="border-top: 1px dashed #e0d5c0;">
                    <p class="text-[10px] tracking-wider mb-1" style="color: #3a7a4d;">BAHASA INDONESIA</p>
                    <p class="text-sm leading-relaxed" style="color: #2a4a3a;">{{ page.translated_id }}</p>
                  </div>
                  <div v-if="page.translated_en" class="pt-1">
                    <p class="text-[10px] tracking-wider mb-1" style="color: #4a6a8a;">ENGLISH</p>
                    <p class="text-xs leading-relaxed" style="color: #2a3a4a;">{{ page.translated_en }}</p>
                  </div>
                </div>
              </div>
              <div v-if="getPages(pdf.id).length === 0" class="mt-2 p-4 text-center text-xs italic" style="color: #a0896a;">Belum ada halaman.</div>
            </div>
          </div>
        </div>
        <div v-if="pdfList.length === 0" class="rounded-lg p-8 text-center" style="background: #faf8f0; border: 1px dashed #e0d5c0;">
          <div class="text-4xl mb-3" style="color: #d4c5a9;">📄</div>
          <p class="text-sm font-medium" style="color: #8b7355;">Belum ada PDF</p>
          <p class="text-xs mt-1" style="color: #a0896a;">Upload PDF untuk memulai OCR dan terjemahan</p>
        </div>
      </div>
    </main>

    <footer class="text-center py-4">
      <div class="max-w-4xl mx-auto px-4">
        <div class="flex items-center justify-center gap-2 text-[10px] tracking-wider" style="color: #a0896a;">
          <span style="border-top: 1px solid #d4c5a9; flex: 1; max-width: 40px;"></span><span>Penerjemah Kitab</span><span style="border-top: 1px solid #d4c5a9; flex: 1; max-width: 40px;"></span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

/* ── Types ── */
interface WordAnalysis { word: string; lemma: string; root: string; pos_type: string; pos_arabic: string; gloss_id: string; gloss_en: string }
interface AnalyzeResponse { original: string; harakat: string; words: WordAnalysis[]; word_count: number }
interface OCRPDFInfo { id: number; filename: string; total_pages: number; uploaded_at: string; pages_processed: number; pages_translated: number }
interface OCRPage { id: number; pdf_id: number; page_number: number; raw_text: string; cleaned_text: string; confidence: number; translated_id: string; translated_en: string }

/* ── Tab state ── */
const activeTab = ref<'analyze' | 'scan'>('analyze')

/* ── Analyze tab ── */
const inputText = ref('')
const result = ref<AnalyzeResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const translating = ref(false)
const translation = ref<{ translation_id: string; translation_en: string } | null>(null)
let _translateId = 0

/* ── Scan PDF tab ── */
const tesseractOk = ref(false)
const tesseractVersion = ref('')
const selectedFile = ref<File | null>(null)
const pdfInfo = ref<{ total_pages: number } | null>(null)
const pageStart = ref(1); const pageEnd = ref(1)
const dragOver = ref(false)
const ocrProcessing = ref(false); const ocrProgress = ref(0); const ocrCurrentPage = ref(0); const ocrTotalPages = ref(0)
const ocrError = ref<string | null>(null); const uploadStatus = ref('Mengupload...')
const pdfList = ref<OCRPDFInfo[]>([]); const pagesCache = ref<Record<number, OCRPage[]>>({})

/* ── Per-page state ── */
const expandedPages = ref<Record<number, boolean>>({})  // starts empty = all collapsed
const pageEdits = ref<Record<number, string>>({})
const editingPages = ref<Record<number, boolean>>({})
const savingPageIds = ref<Record<number, boolean>>({})
const tashkeelingPageIds = ref<Record<number, boolean>>({})
const translatingPdfId = ref<number | null>(null)
const translatingPageId = ref<number | null>(null)

const config = useRuntimeConfig()

/* ── POS badge colors ── */
const posColors: Record<string, string> = {
  noun: 'noun-badge', verb: 'verb-badge', prep: 'prep-badge', conj: 'prep-badge',
  part: 'part-badge', pron: 'pron-badge', adj: 'adj-badge', adv: 'adv-badge',
  det: 'det-badge', dem: 'dem-badge', neg: 'neg-badge', interr: 'interr-badge',
  num: 'num-badge', noun_num: 'num-badge', noun_quant: 'num-badge',
  rel: 'rel-badge', noun_prop: 'noun-badge', abbrev: 'part-badge',
}
function posBadgeClass(type: string): string { return posColors[type] || 'default-badge' }

/* ── Analyze functions ── */
async function analyze() {
  loading.value = true; error.value = null; result.value = null
  try {
    const res = await fetch(`${config.public.apiBase}/api/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: inputText.value }) })
    if (!res.ok) throw new Error(`Error: ${res.status}`)
    result.value = await res.json()
    translateText(inputText.value)
  } catch (e) { error.value = e instanceof Error ? e.message : 'Gagal' }
  finally { loading.value = false }
}
async function translateText(text: string) {
  const requestId = ++_translateId; translating.value = true; translation.value = null
  try {
    const res = await fetch(`${config.public.apiBase}/api/translate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) })
    if (!res.ok) return; const data = await res.json(); if (requestId !== _translateId) return
    translation.value = { translation_id: data.translation_id, translation_en: data.translation_en }
  } catch { /* ignore */ } finally { translating.value = false }
}
async function copyResult() { if (result.value?.harakat) { await navigator.clipboard.writeText(result.value.harakat) } }

/* ── Accordion ── */
function toggleExpand(pageId: number) { expandedPages.value[pageId] = !expandedPages.value[pageId] }

/* ── OCR helpers ── */
async function checkTesseract() {
  try { const res = await fetch(`${config.public.apiBase}/api/ocr/health`); const d = await res.json(); tesseractOk.value = d.tesseract_installed; tesseractVersion.value = d.tesseract_version } catch { tesseractOk.value = false }
}
async function loadPdfList() { try { const res = await fetch(`${config.public.apiBase}/api/ocr/pdfs`); if (res.ok) pdfList.value = await res.json() } catch { /* ignore */ } }
async function loadPages(pdfId: number) { try { const res = await fetch(`${config.public.apiBase}/api/ocr/pages/${pdfId}`); if (res.ok) { const d = await res.json(); pagesCache.value[pdfId] = d.pages } } catch { /* ignore */ } }
function getPages(pdfId: number): OCRPage[] { return pagesCache.value[pdfId] || [] }

/* ── Edit functions ── */
function getPageText(page: OCRPage): string { return pageEdits.value[page.id] !== undefined ? pageEdits.value[page.id] : (page.cleaned_text || page.raw_text || '') }
function getEditedText(page: OCRPage): string { const e = pageEdits.value[page.id]; return (e !== undefined && e.trim()) ? e.trim() : (page.cleaned_text || page.raw_text || '').trim() }
function updatePageEdit(id: number, text: string) { pageEdits.value[id] = text }
function getEditLength(page: OCRPage): number { const e = pageEdits.value[page.id]; return e !== undefined ? e.length : (page.cleaned_text || page.raw_text || '').length }
function toggleEdit(id: number, editing: boolean) { editingPages.value[id] = editing }

/* ── Save ── */
async function savePageText(page: OCRPage) {
  const text = getEditedText(page); if (!text) return
  savingPageIds.value[page.id] = true
  try {
    const res = await fetch(`${config.public.apiBase}/api/ocr/save-page`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ page_id: page.id, text }) })
    if (res.ok) { toggleEdit(page.id, false); for (const [pid, pages] of Object.entries(pagesCache.value)) { if (pages.some(p => p.id === page.id)) { await loadPages(Number(pid)); break } } }
  } catch { /* ignore */ } finally { savingPageIds.value[page.id] = false }
}

/* ── Tashkeel ── */
async function tashkeelPageText(page: OCRPage) {
  const text = getEditedText(page); if (!text) return
  tashkeelingPageIds.value[page.id] = true
  try {
    let res = await fetch(`${config.public.apiBase}/api/ocr/tashkeel-page`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) })
    if (!res.ok) { res = await fetch(`${config.public.apiBase}/api/tashkeel`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) }) }
    if (res.ok) { const data = await res.json(); updatePageEdit(page.id, data.harakat) }
  } catch { /* ignore */ } finally { tashkeelingPageIds.value[page.id] = false }
}

/* ── Translate page ── */
async function translatePage(pageId: number, _pn: number, text: string) {
  if (!text) return; translatingPageId.value = pageId
  try {
    const res = await fetch(`${config.public.apiBase}/api/ocr/translate-page`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ page_id: pageId, text }) })
    if (res.ok) { for (const [pid, pages] of Object.entries(pagesCache.value)) { if (pages.some(p => p.id === pageId)) { await loadPages(Number(pid)); toggleEdit(pageId, false); break } } }
  } catch { /* ignore */ } finally { translatingPageId.value = null }
}

/* ── Bulk translate ── */
async function translatePdf(pdfId: number) {
  translatingPdfId.value = pdfId
  try { const res = await fetch(`${config.public.apiBase}/api/ocr/translate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pdf_id: pdfId }) }); if (res.ok) { await loadPdfList(); await loadPages(pdfId) } } catch { /* ignore */ }
  finally { translatingPdfId.value = null }
}

/* ── Delete ── */
async function deletePdf(pdfId: number) {
  try { const res = await fetch(`${config.public.apiBase}/api/ocr/delete/${pdfId}`, { method: 'POST' }); if (res.ok) { delete pagesCache.value[pdfId]; await loadPdfList() } } catch { /* ignore */ }
}

/* ── Upload ── */
function handleFileSelect(event: Event) { const input = event.target as HTMLInputElement; if (input.files?.[0]) setFile(input.files[0]) }
function handleDrop(event: DragEvent) { dragOver.value = false; if (event.dataTransfer?.files[0]) setFile(event.dataTransfer.files[0]) }
function setFile(file: File) { selectedFile.value = file; pdfInfo.value = null }

async function uploadAndProcess() {
  if (!selectedFile.value || !tesseractOk.value) return
  ocrProcessing.value = true; ocrError.value = null; ocrProgress.value = 0
  try {
    uploadStatus.value = 'Mengupload...'
    const fd = new FormData(); fd.append('file', selectedFile.value)
    const uRes = await fetch(`${config.public.apiBase}/api/ocr/upload`, { method: 'POST', body: fd })
    if (!uRes.ok) throw new Error('Gagal upload')
    const uData = await uRes.json(); const pdfId = uData.pdf_id; const maxPages = uData.total_pages
    pageStart.value = 1; pageEnd.value = maxPages
    ocrTotalPages.value = maxPages; uploadStatus.value = 'OCR...'
    for (let pg = 1; pg <= maxPages; pg++) {
      ocrCurrentPage.value = pg; ocrProgress.value = pg / maxPages; uploadStatus.value = `OCR hal ${pg}/${maxPages}...`
      const pRes = await fetch(`${config.public.apiBase}/api/ocr/process`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pdf_id: pdfId, page_start: pg, page_end: pg }) })
      if (!pRes.ok) throw new Error('Gagal OCR')
    }
    ocrProgress.value = 1; await loadPdfList(); await loadPages(pdfId); selectedFile.value = null; pdfInfo.value = null
  } catch (e) { ocrError.value = e instanceof Error ? e.message : 'Gagal' }
  finally { ocrProcessing.value = false }
}

onMounted(() => { checkTesseract(); loadPdfList() })
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');
.font-arabic { font-family: 'Amiri', 'Traditional Arabic', serif !important; }

/* POS badge colors */
.noun-badge { background: #dcfce7; color: #166534; }
.verb-badge { background: #ffedd5; color: #9a3412; }
.prep-badge { background: #f3e8ff; color: #6b21a8; }
.part-badge { background: #f3f4f6; color: #4b5563; }
.pron-badge { background: #fce7f3; color: #9d174d; }
.adj-badge { background: #d1fae5; color: #065f46; }
.adv-badge { background: #ccfbf1; color: #115e59; }
.det-badge { background: #e0e7ff; color: #3730a3; }
.dem-badge { background: #fce7f3; color: #9d174d; }
.neg-badge { background: #fee2e2; color: #991b1b; }
.interr-badge { background: #cffafe; color: #155e75; }
.num-badge { background: #ecfccb; color: #3f6212; }
.rel-badge { background: #f3e8ff; color: #6b21a8; }
.default-badge { background: #f3f4f6; color: #4b5563; }

/* Word card animations */
.word-card { transition: all 0.3s ease; animation: kitabReveal 0.5s ease-out both; }
.word-card:hover { transform: translateY(-2px); z-index: 10; }
.word-card:hover > div { box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 4px; }
@keyframes kitabReveal { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
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

/* Hover states */
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
