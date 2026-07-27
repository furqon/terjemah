import { defineComponent, ref, mergeProps, useSSRContext } from 'vue';
import { ssrRenderAttrs, ssrRenderStyle, ssrInterpolate, ssrIncludeBooleanAttr, ssrRenderList, ssrRenderAttr, ssrRenderClass } from 'vue/server-renderer';

const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "index",
  __ssrInlineRender: true,
  setup(__props) {
    const activeTab = ref("analyze");
    const inputText = ref("");
    const result = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const translating = ref(false);
    const translation = ref(null);
    const tesseractOk = ref(false);
    const tesseractVersion = ref("");
    const selectedFile = ref(null);
    const pdfInfo = ref(null);
    const pageStart = ref(1);
    const pageEnd = ref(1);
    const dragOver = ref(false);
    const ocrProcessing = ref(false);
    const ocrProgress = ref(0);
    const ocrCurrentPage = ref(0);
    const ocrTotalPages = ref(0);
    const ocrError = ref(null);
    const uploadStatus = ref("Mengupload...");
    const pdfList = ref([]);
    const pagesCache = ref({});
    const expandedPages = ref({});
    const pageEdits = ref({});
    const editingPages = ref({});
    const savingPageIds = ref({});
    const tashkeelingPageIds = ref({});
    const translatingPdfId = ref(null);
    const translatingPageId = ref(null);
    const paragraphsCache = ref({});
    const paragraphExpandIds = ref({});
    const posColors = {
      noun: "noun-badge",
      verb: "verb-badge",
      prep: "prep-badge",
      conj: "prep-badge",
      part: "part-badge",
      pron: "pron-badge",
      adj: "adj-badge",
      adv: "adv-badge",
      det: "det-badge",
      dem: "dem-badge",
      neg: "neg-badge",
      interr: "interr-badge",
      num: "num-badge",
      noun_num: "num-badge",
      noun_quant: "num-badge",
      rel: "rel-badge",
      noun_prop: "noun-badge",
      abbrev: "part-badge"
    };
    function posBadgeClass(type) {
      return posColors[type] || "default-badge";
    }
    function getPages(pdfId) {
      return pagesCache.value[pdfId] || [];
    }
    function getPageText(page) {
      return pageEdits.value[page.id] !== void 0 ? pageEdits.value[page.id] : page.cleaned_text || page.raw_text || "";
    }
    function getEditLength(page) {
      const e = pageEdits.value[page.id];
      return e !== void 0 ? e.length : (page.cleaned_text || page.raw_text || "").length;
    }
    return (_ctx, _push, _parent, _attrs) => {
      _push(`<div${ssrRenderAttrs(mergeProps({
        class: "min-h-screen",
        style: { "background": "#f5f0e8" }
      }, _attrs))}><header class="relative overflow-hidden" style="${ssrRenderStyle({ "background": "linear-gradient(135deg, #1a3a2a 0%, #2d5a3d 50%, #1a3a2a 100%)" })}"><div class="h-2" style="${ssrRenderStyle({ "background": "repeating-linear-gradient(90deg, #c9a84c 0px, #c9a84c 4px, #1a3a2a 4px, #1a3a2a 6px, #c9a84c 6px, #c9a84c 10px, #1a3a2a 10px, #1a3a2a 12px)" })}"></div><div class="h-1" style="${ssrRenderStyle({ "background": "linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%)", "opacity": "0.5" })}"></div><div class="max-w-4xl mx-auto px-4 py-5 text-center relative"><div class="absolute left-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\uFD3F</div><div class="absolute right-4 top-1/2 -translate-y-1/2 text-2xl opacity-30 select-none" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\uFD3E</div><h1 class="text-2xl font-bold tracking-wide" style="${ssrRenderStyle({ "font-family": "'Amiri', 'Traditional Arabic', serif", "color": "#f5f0e8" })}">Penerjemah Kitab</h1><p class="text-xs mt-1 tracking-wider" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\u2726 Analisis + OCR + Terjemahan \u2726</p></div><div class="h-1" style="${ssrRenderStyle({ "background": "linear-gradient(90deg, transparent 0%, #c9a84c 20%, #c9a84c 80%, transparent 100%)", "opacity": "0.5" })}"></div></header><main class="max-w-4xl mx-auto px-4 py-4"><div class="flex gap-0 border-b mb-4" style="${ssrRenderStyle({ "border-color": "#d4c5a9" })}"><button class="px-5 py-2.5 text-sm font-medium rounded-t-lg transition-all" style="${ssrRenderStyle(activeTab.value === "analyze" ? { background: "#fffdf5", color: "#2d5a3d", border: "1px solid #d4c5a9", borderBottom: "1px solid #fffdf5", marginBottom: "-1px" } : { color: "#a0896a", border: "1px solid transparent" })}"><span class="flex items-center gap-1.5"><span>\u{1F4D6}</span> Analisis Teks</span></button><button class="px-5 py-2.5 text-sm font-medium rounded-t-lg transition-all" style="${ssrRenderStyle(activeTab.value === "scan" ? { background: "#fffdf5", color: "#2d5a3d", border: "1px solid #d4c5a9", borderBottom: "1px solid #fffdf5", marginBottom: "-1px" } : { color: "#a0896a", border: "1px solid transparent" })}"><span class="flex items-center gap-1.5"><span>\u{1F4C4}</span> Scan PDF</span></button></div>`);
      if (activeTab.value === "analyze") {
        _push(`<div><div class="mb-3 rounded-lg" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #e8dcc8", "box-shadow": "0 1px 3px rgba(0,0,0,0.05)" })}"><div class="p-3"><label class="block text-xs font-medium mb-1 tracking-wider" style="${ssrRenderStyle({ "color": "#8b7355" })}">Tulis Teks Arab</label><textarea placeholder="\u064A\u0643\u062A\u0628 \u0627\u0644\u0637\u0627\u0644\u0628 \u0627\u0644\u062F\u0631\u0633 \u0641\u064A \u0627\u0644\u0645\u0643\u062A\u0628\u0629..." dir="rtl" class="w-full h-24 p-3 rounded-lg text-base font-arabic transition-colors resize-y" style="${ssrRenderStyle({ "background": "#faf8f0", "border": "1px solid #e0d5c0", "color": "#3a2a1a" })}">${ssrInterpolate(inputText.value)}</textarea><button${ssrIncludeBooleanAttr(loading.value || !inputText.value.trim()) ? " disabled" : ""} class="mt-2 w-full font-medium py-2 px-4 rounded-lg text-sm tracking-wider transition-all duration-200 disabled:cursor-not-allowed" style="${ssrRenderStyle([{ "background": "linear-gradient(135deg, #2d5a3d, #1a3a2a)", "color": "#f5f0e8" }, loading.value || !inputText.value.trim() ? { opacity: 0.5 } : {}])}">`);
        if (loading.value) {
          _push(`<span class="flex items-center justify-center gap-1.5"><svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Memproses...</span>`);
        } else {
          _push(`<span>${ssrInterpolate("\u263E")} Analisis Teks</span>`);
        }
        _push(`</button></div></div>`);
        if (error.value) {
          _push(`<div class="px-3 py-2 rounded-lg mb-3 text-sm" style="${ssrRenderStyle({ "background": "#fef2f2", "border": "1px solid #fecaca", "color": "#991b1b" })}">${ssrInterpolate(error.value)}</div>`);
        } else {
          _push(`<!---->`);
        }
        if (result.value) {
          _push(`<div class="space-y-3"><div class="relative overflow-hidden rounded-lg" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #d4c5a9", "box-shadow": "0 2px 8px rgba(0,0,0,0.06)" })}"><div class="h-1" style="${ssrRenderStyle({ "background": "linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%)" })}"></div><div class="text-center pt-4 pb-2 px-4"><div class="text-xs tracking-widest" style="${ssrRenderStyle({ "color": "#8b7355" })}">\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u064E\u0651\u0647\u0650 \u0627\u0644\u0631\u064E\u0651\u062D\u0652\u0645\u064E\u0646\u0650 \u0627\u0644\u0631\u064E\u0651\u062D\u0650\u064A\u0645\u0650</div><div class="mt-1" style="${ssrRenderStyle({ "border-top": "1px solid #e8dcc8", "width": "60px", "margin": "0 auto" })}"></div><div class="mt-2 flex items-center justify-center gap-2 text-xs" style="${ssrRenderStyle({ "color": "#a0896a" })}"><span>\u25B8</span><span class="tracking-wider">Teks Arab</span><span>\u25C2</span></div></div><div class="mx-4 p-4 text-center rounded" style="${ssrRenderStyle({ "background": "#faf8f0", "border": "1px solid #e0d5c0" })}"><div class="flex flex-wrap justify-center gap-x-4 gap-y-1" dir="rtl"><!--[-->`);
          ssrRenderList(result.value.words, (word, i) => {
            _push(`<span class="text-3xl md:text-4xl font-arabic leading-relaxed transition-all duration-200 hover:scale-105 hover:text-[#c9a84c] cursor-default" style="${ssrRenderStyle({ "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif", "text-shadow": "0 1px 1px rgba(0,0,0,0.05)" })}"${ssrRenderAttr("title", word.gloss_id)}>${ssrInterpolate(word.word)}`);
            if (i < result.value.words.length - 1) {
              _push(`<span class="text-lg opacity-30 select-none" style="${ssrRenderStyle({ "color": "#a0896a" })}"></span>`);
            } else {
              _push(`<!---->`);
            }
            _push(`</span>`);
          });
          _push(`<!--]--></div></div><div class="flex items-center justify-center gap-2 px-4 py-3" style="${ssrRenderStyle({ "color": "#c9a84c" })}"><span style="${ssrRenderStyle({ "border-top": "1px solid", "flex": "1", "max-width": "60px", "opacity": "0.5" })}"></span><span style="${ssrRenderStyle({ "font-size": "16px", "line-height": "1" })}">\u25C8</span><span style="${ssrRenderStyle({ "border-top": "1px solid", "flex": "1", "max-width": "60px", "opacity": "0.5" })}"></span></div><div class="text-center px-4 pb-2"><button class="text-[10px] tracking-wider py-1 px-3 rounded transition-all duration-200" style="${ssrRenderStyle({ "color": "#8b7355", "border": "1px solid #e0d5c0", "background": "#faf8f0" })}">Salin Teks</button></div><div class="px-4 pb-1"><div class="flex items-center justify-center gap-2 text-xs" style="${ssrRenderStyle({ "color": "#a0896a" })}"><span>\u25B8</span><span class="tracking-wider">Analisis Per Kata</span><span>\u25C2</span></div></div><div class="px-4 pb-4"><div class="flex flex-wrap justify-center gap-1" style="${ssrRenderStyle({ "direction": "rtl" })}"><!--[-->`);
          ssrRenderList(result.value.words, (word, i) => {
            _push(`<div class="word-card flex flex-col items-center rounded-sm transition-all duration-300" style="${ssrRenderStyle({ "direction": "ltr", "min-width": "90px", "max-width": "130px", "flex": "1 0 auto" })}"><div class="w-full text-center px-1.5 py-1.5" style="${ssrRenderStyle({ "background": "#faf8f0" })}"><p class="text-xl font-arabic leading-tight" dir="rtl" style="${ssrRenderStyle({ "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif" })}">${ssrInterpolate(word.word)}</p><p class="text-[11px] font-medium mt-0.5" style="${ssrRenderStyle({ "color": "#5a7a4a" })}">${ssrInterpolate(word.lemma)}</p>`);
            if (word.root && word.root !== "\u2014") {
              _push(`<p class="text-[9px]" style="${ssrRenderStyle({ "color": "#a0896a" })}">(${ssrInterpolate(word.root)})</p>`);
            } else {
              _push(`<!---->`);
            }
            _push(`<span class="${ssrRenderClass([posBadgeClass(word.pos_type), "inline-block mt-[2px] px-1.5 py-[1px] rounded-sm text-[9px] font-bold"])}">${ssrInterpolate(word.pos_arabic)}</span><div class="mt-1 leading-tight">`);
            if (word.gloss_id) {
              _push(`<p class="text-[10px] font-medium" style="${ssrRenderStyle({ "color": "#3a7a4d" })}" title="Indonesian">${ssrInterpolate(word.gloss_id)}</p>`);
            } else {
              _push(`<!---->`);
            }
            if (word.gloss_en) {
              _push(`<p class="text-[9px]" style="${ssrRenderStyle({ "color": "#6a8aaa" })}" title="English">${ssrInterpolate(word.gloss_en)}</p>`);
            } else {
              _push(`<!---->`);
            }
            _push(`</div></div></div>`);
          });
          _push(`<!--]--></div></div><div class="text-center pb-3"><div style="${ssrRenderStyle({ "border-top": "1px solid #e8dcc8", "width": "40%", "margin": "0 auto" })}"></div><p class="text-[10px] mt-2 tracking-wider" style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(result.value.word_count)} kata \u2014 ${ssrInterpolate(result.value.original.length)} karakter</p></div><div class="h-1" style="${ssrRenderStyle({ "background": "linear-gradient(90deg, #d4c5a9 0%, #c9a84c 30%, #c9a84c 70%, #d4c5a9 100%)" })}"></div></div>`);
          if (translating.value) {
            _push(`<div class="rounded-lg p-4 text-center" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #d4c5a9" })}"><p class="text-sm italic" style="${ssrRenderStyle({ "color": "#a0896a" })}">Menerjemahkan...</p></div>`);
          } else {
            _push(`<!---->`);
          }
          if (translation.value) {
            _push(`<div class="rounded-lg overflow-hidden" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #d4c5a9" })}"><div class="h-1" style="${ssrRenderStyle({ "background": "linear-gradient(90deg, #d4c5a9 0%, #3a7a4d 30%, #3a7a4d 70%, #d4c5a9 100%)" })}"></div><div class="p-4"><div class="flex items-center justify-center gap-2 text-xs mb-3" style="${ssrRenderStyle({ "color": "#a0896a" })}"><span>\u25B8</span><span class="tracking-wider">Terjemahan Lengkap</span><span>\u25C2</span></div><div class="space-y-3"><div class="text-right" dir="rtl"><p class="text-[10px] tracking-wider mb-1" style="${ssrRenderStyle({ "color": "#8b7355" })}">TEKS ARAB</p><p class="text-xl font-arabic leading-relaxed" style="${ssrRenderStyle({ "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif" })}">${ssrInterpolate(result.value.harakat)}</p></div><div style="${ssrRenderStyle({ "border-top": "1px dashed #e0d5c0" })}"></div><div><p class="text-[10px] tracking-wider mb-1" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">BAHASA INDONESIA</p><p class="text-base leading-relaxed" style="${ssrRenderStyle({ "color": "#2a4a3a" })}">${ssrInterpolate(translation.value.translation_id)}</p></div><div style="${ssrRenderStyle({ "border-top": "1px dashed #e0d5c0" })}"></div><div><p class="text-[10px] tracking-wider mb-1" style="${ssrRenderStyle({ "color": "#4a6a8a" })}">ENGLISH</p><p class="text-base leading-relaxed" style="${ssrRenderStyle({ "color": "#2a3a4a" })}">${ssrInterpolate(translation.value.translation_en)}</p></div></div></div></div>`);
          } else {
            _push(`<!---->`);
          }
          _push(`<details class="group rounded-lg overflow-hidden" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #d4c5a9" })}"><summary class="cursor-pointer px-4 py-2.5 text-xs tracking-wider font-medium flex items-center justify-between transition-colors" style="${ssrRenderStyle({ "color": "#5a7a4a" })}"><span class="flex items-center gap-1.5"><span class="transition-transform duration-200 group-open:rotate-90 text-sm" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\u25B8</span> Detail Lengkap</span><span style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(result.value.word_count)} kata</span></summary><div class="px-4 pb-3 overflow-x-auto"><table class="w-full text-xs border-collapse"><thead><tr style="${ssrRenderStyle({ "border-bottom": "1px solid #e0d5c0" })}"><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">#</th><th class="p-2 text-right font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Arab</th><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Lemma</th><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Akar</th><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Jenis</th><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">ID</th><th class="p-2 text-left font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">EN</th></tr></thead><tbody><!--[-->`);
          ssrRenderList(result.value.words, (word, i) => {
            _push(`<tr class="transition-colors" style="${ssrRenderStyle({ "border-bottom": "1px solid #f0eadc" })}"><td class="p-2" style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(i + 1)}</td><td class="p-2 font-arabic text-right text-sm" dir="rtl" style="${ssrRenderStyle({ "color": "#3a2a1a" })}">${ssrInterpolate(word.word)}</td><td class="p-2 font-medium" style="${ssrRenderStyle({ "color": "#5a7a4a" })}">${ssrInterpolate(word.lemma)}</td><td class="p-2" style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(word.root !== "\u2014" ? word.root : "\u2014")}</td><td class="p-2"><span class="${ssrRenderClass([posBadgeClass(word.pos_type), "px-1.5 py-0.5 rounded-sm text-[10px] font-bold"])}">${ssrInterpolate(word.pos_arabic)}</span></td><td class="p-2" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">${ssrInterpolate(word.gloss_id || "\u2014")}</td><td class="p-2" style="${ssrRenderStyle({ "color": "#5a7a8a" })}">${ssrInterpolate(word.gloss_en || "\u2014")}</td></tr>`);
          });
          _push(`<!--]--></tbody></table></div></details></div>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div>`);
      } else {
        _push(`<!---->`);
      }
      if (activeTab.value === "scan") {
        _push(`<div class="space-y-4"><div class="px-3 py-2 rounded-lg text-xs flex items-center gap-2" style="${ssrRenderStyle(tesseractOk.value ? { background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534" } : { background: "#fefce8", border: "1px solid #fef08a", color: "#854d0e" })}"><span>${ssrInterpolate(tesseractOk.value ? "\u2713" : "\u26A0")}</span><span><strong>Tesseract:</strong> ${ssrInterpolate(tesseractOk.value ? tesseractVersion.value : "Belum terinstal")}</span></div><div class="rounded-lg" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #e8dcc8", "box-shadow": "0 1px 3px rgba(0,0,0,0.05)" })}"><div class="p-4"><h2 class="text-sm font-bold mb-3" style="${ssrRenderStyle({ "color": "#3a2a1a" })}"><span>\u{1F4C1}</span> Upload PDF</h2><div class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors mb-3" style="${ssrRenderStyle(dragOver.value ? { borderColor: "#c9a84c", background: "#fdf8ec" } : { borderColor: "#e0d5c0", background: "#faf8f0" })}"><input type="file" accept=".pdf" class="hidden"><div class="text-3xl mb-2" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\u{1F4C4}</div><p class="text-sm font-medium" style="${ssrRenderStyle({ "color": "#3a2a1a" })}">${ssrInterpolate(selectedFile.value ? selectedFile.value.name : "Klik atau seret PDF")}</p>`);
        if (!selectedFile.value) {
          _push(`<p class="text-xs mt-1" style="${ssrRenderStyle({ "color": "#a0896a" })}">Format PDF, maks 50MB</p>`);
        } else {
          _push(`<!---->`);
        }
        if (selectedFile.value && pdfInfo.value) {
          _push(`<p class="text-xs mt-1" style="${ssrRenderStyle({ "color": "#5a7a4a" })}">${ssrInterpolate(pdfInfo.value.total_pages)} halaman</p>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div><div class="flex items-end gap-3"><div><label class="text-[10px] block mb-1 tracking-wider" style="${ssrRenderStyle({ "color": "#8b7355" })}">Dari</label><input${ssrRenderAttr("value", pageStart.value)} type="number" min="1" class="w-16 p-2 border rounded text-sm text-center" style="${ssrRenderStyle({ "border-color": "#e0d5c0", "background": "#faf8f0", "color": "#3a2a1a" })}"></div><div><label class="text-[10px] block mb-1 tracking-wider" style="${ssrRenderStyle({ "color": "#8b7355" })}">Sampai</label><input${ssrRenderAttr("value", pageEnd.value)} type="number" min="1" class="w-16 p-2 border rounded text-sm text-center" style="${ssrRenderStyle({ "border-color": "#e0d5c0", "background": "#faf8f0", "color": "#3a2a1a" })}"></div><button${ssrIncludeBooleanAttr(ocrProcessing.value || !selectedFile.value || !tesseractOk.value) ? " disabled" : ""} class="flex-1 py-2.5 rounded-lg text-sm font-medium tracking-wider transition-all disabled:cursor-not-allowed" style="${ssrRenderStyle([{ "background": "linear-gradient(135deg, #2d5a3d, #1a3a2a)", "color": "#f5f0e8" }, ocrProcessing.value || !selectedFile.value || !tesseractOk.value ? { opacity: 0.5 } : {}])}">`);
        if (ocrProcessing.value) {
          _push(`<span class="flex items-center justify-center gap-1.5"><svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> ${ssrInterpolate(uploadStatus.value)}</span>`);
        } else {
          _push(`<span>${ssrInterpolate("\u263E")} Proses OCR</span>`);
        }
        _push(`</button></div>`);
        if (ocrProcessing.value) {
          _push(`<div class="mt-3"><div class="flex justify-between text-xs mb-1" style="${ssrRenderStyle({ "color": "#8b7355" })}"><span>Hal ${ssrInterpolate(ocrCurrentPage.value)}/${ssrInterpolate(ocrTotalPages.value)}</span><span>${ssrInterpolate(Math.round(ocrProgress.value * 100))}%</span></div><div class="h-2 rounded-full overflow-hidden" style="${ssrRenderStyle({ "background": "#e0d5c0" })}"><div class="h-full rounded-full transition-all" style="${ssrRenderStyle([{ "background": "linear-gradient(90deg, #c9a84c, #2d5a3d)" }, { width: ocrProgress.value * 100 + "%" }])}"></div></div></div>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div></div>`);
        if (ocrError.value) {
          _push(`<div class="px-3 py-2 rounded-lg text-sm" style="${ssrRenderStyle({ "background": "#fef2f2", "border": "1px solid #fecaca", "color": "#991b1b" })}">${ssrInterpolate(ocrError.value)}</div>`);
        } else {
          _push(`<!---->`);
        }
        if (pdfList.value.length > 0) {
          _push(`<div class="space-y-3"><!--[-->`);
          ssrRenderList(pdfList.value, (pdf) => {
            _push(`<div class="rounded-lg overflow-hidden" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #d4c5a9" })}"><div class="px-4 py-3 flex items-center justify-between" style="${ssrRenderStyle({ "background": "#faf8f0", "border-bottom": "1px solid #e8dcc8" })}"><div class="flex items-center gap-2"><span class="text-lg">\u{1F4C4}</span><div><h3 class="text-sm font-semibold" style="${ssrRenderStyle({ "color": "#3a2a1a" })}">${ssrInterpolate(pdf.filename)}</h3><p class="text-[10px]" style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(pdf.total_pages)} hal \u2022 ${ssrInterpolate(pdf.pages_processed)} diproses \u2022 ${ssrInterpolate(pdf.pages_translated)} terjemah</p></div></div><div class="flex gap-1.5">`);
            if (pdf.pages_processed > 0 && pdf.pages_translated < pdf.pages_processed) {
              _push(`<button${ssrIncludeBooleanAttr(translatingPdfId.value === pdf.id) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50" style="${ssrRenderStyle({ "background": "#c9a84c", "color": "white" })}">${ssrInterpolate(translatingPdfId.value === pdf.id ? "..." : "Terjemah Semua")}</button>`);
            } else {
              _push(`<!---->`);
            }
            _push(`<button class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all" style="${ssrRenderStyle({ "background": "#fef2f2", "color": "#991b1b", "border": "1px solid #fecaca" })}">Hapus</button></div></div><div class="px-4 pb-3"><!--[-->`);
            ssrRenderList(getPages(pdf.id), (page) => {
              _push(`<div class="mt-2 rounded-lg overflow-hidden" style="${ssrRenderStyle({ "border": "1px solid #e0d5c0" })}"><div class="flex items-center justify-between px-3 py-2 cursor-pointer select-none transition-colors" style="${ssrRenderStyle({ "background": "#faf8f0" })}"><div class="flex items-center gap-2"><span class="text-xs inline-block transition-transform duration-200" style="${ssrRenderStyle([{ transform: expandedPages.value[page.id] ? "rotate(90deg)" : "rotate(0deg)" }, { "color": "#a0896a" }])}">\u25B8</span><span class="text-xs font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Halaman ${ssrInterpolate(page.page_number)}</span></div><div class="flex items-center gap-1.5">`);
              if (pageEdits.value[page.id] !== void 0 && !editingPages.value[page.id]) {
                _push(`<span class="text-[9px]" style="${ssrRenderStyle({ "color": "#c9a84c" })}">\u270E</span>`);
              } else {
                _push(`<!---->`);
              }
              _push(`<span class="text-[10px] px-1.5 py-0.5 rounded" style="${ssrRenderStyle(page.confidence >= 0.8 ? { background: "#dcfce7", color: "#166534" } : page.confidence >= 0.5 ? { background: "#fef9c3", color: "#854d0e" } : { background: "#fee2e2", color: "#991b1b" })}">${ssrInterpolate(Math.round(page.confidence * 100))}%</span>`);
              if (page.translated_id) {
                _push(`<span class="text-[9px]" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">\u2713</span>`);
              } else {
                _push(`<!---->`);
              }
              _push(`</div></div>`);
              if (expandedPages.value[page.id]) {
                _push(`<div class="px-3 py-3" style="${ssrRenderStyle({ "background": "#fffdf5", "border-top": "1px solid #e0d5c0" })}">`);
                if (!editingPages.value[page.id]) {
                  _push(`<div><div class="mb-2" dir="rtl"><p class="text-[10px] tracking-wider mb-1" style="${ssrRenderStyle({ "color": "#8b7355" })}">TEKS ARAB</p><p class="text-base font-arabic leading-relaxed" style="${ssrRenderStyle({ "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif" })}">${ssrInterpolate(getPageText(page))}</p></div><div class="flex justify-end gap-1.5 flex-wrap"><button class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all flex items-center gap-1" style="${ssrRenderStyle({ "background": "#e0d5c0", "color": "#3a2a1a" })}">\u270E Edit</button><button${ssrIncludeBooleanAttr(tashkeelingPageIds.value[page.id]) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1" style="${ssrRenderStyle({ "background": "#6b21a8", "color": "white" })}">`);
                  if (tashkeelingPageIds.value[page.id]) {
                    _push(`<span><svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg></span>`);
                  } else {
                    _push(`<span>${ssrInterpolate("\u25CC")} Tashkeel</span>`);
                  }
                  _push(`</button><button${ssrIncludeBooleanAttr(translatingPageId.value === page.id) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1" style="${ssrRenderStyle({ "background": "#c9a84c", "color": "white" })}">`);
                  if (translatingPageId.value === page.id) {
                    _push(`<span><svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg></span>`);
                  } else {
                    _push(`<span>${ssrInterpolate("\u263E")} Terjemah</span>`);
                  }
                  _push(`</button></div></div>`);
                } else {
                  _push(`<div><div class="mb-2"><div class="flex items-center justify-between mb-1"><p class="text-[10px] tracking-wider" style="${ssrRenderStyle({ "color": "#8b7355" })}">EDIT TEKS ARAB</p><span class="text-[9px]" style="${ssrRenderStyle({ "color": "#a0896a" })}">${ssrInterpolate(getEditLength(page))} karakter</span></div><textarea dir="rtl" class="w-full p-2.5 rounded-lg text-base font-arabic leading-relaxed resize-y transition-colors" style="${ssrRenderStyle({ "background": "#fffdf5", "border": "1px solid #c9a84c", "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif", "min-height": "80px" })}">${ssrInterpolate(getPageText(page))}</textarea></div><div class="flex justify-end gap-1.5 flex-wrap"><button${ssrIncludeBooleanAttr(savingPageIds.value[page.id]) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1" style="${ssrRenderStyle({ "background": "#2d5a3d", "color": "white" })}">${ssrInterpolate(savingPageIds.value[page.id] ? "Menyimpan..." : "\u{1F4BE} Save")}</button><button${ssrIncludeBooleanAttr(tashkeelingPageIds.value[page.id]) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1" style="${ssrRenderStyle({ "background": "#6b21a8", "color": "white" })}">${ssrInterpolate(tashkeelingPageIds.value[page.id] ? "Tashkeel..." : "\u25CC Tashkeel")}</button><button${ssrIncludeBooleanAttr(translatingPageId.value === page.id) ? " disabled" : ""} class="text-[10px] px-2.5 py-1.5 rounded font-medium transition-all disabled:opacity-50 flex items-center gap-1" style="${ssrRenderStyle({ "background": "#c9a84c", "color": "white" })}">`);
                  if (translatingPageId.value === page.id) {
                    _push(`<span><svg class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg></span>`);
                  } else {
                    _push(`<span>${ssrInterpolate("\u263E")} Terjemah</span>`);
                  }
                  _push(`</button></div></div>`);
                }
                if (paragraphsCache.value[page.id] && paragraphsCache.value[page.id].length > 0) {
                  _push(`<div class="mt-2"><div style="${ssrRenderStyle({ "border-top": "1px dashed #d4c5a9" })}" class="mb-2"></div><div class="flex items-center justify-between mb-2"><p class="text-[10px] tracking-wider" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">\u{1F4DC} TERJEMAHAN PER PARAGRAF</p><button class="text-[9px] px-2 py-0.5 rounded transition-all" style="${ssrRenderStyle({ "background": "#faf8f0", "border": "1px solid #e0d5c0", "color": "#8b7355" })}">${ssrInterpolate(paragraphExpandIds.value[page.id] ? "\u25B2 Sembunyikan" : "\u25BC Tampilkan " + paragraphsCache.value[page.id].length + " paragraf")}</button></div>`);
                  if (paragraphExpandIds.value[page.id]) {
                    _push(`<div><!--[-->`);
                    ssrRenderList(paragraphsCache.value[page.id], (para, pi) => {
                      _push(`<div class="mb-2 rounded-lg overflow-hidden transition-all duration-200" style="${ssrRenderStyle({
                        background: pi % 2 === 0 ? "#faf8f0" : "#fffdf5",
                        border: "1px solid #e8dcc8"
                      })}"><div class="px-3 py-2 flex items-start gap-2"><span class="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full text-[9px] font-bold" style="${ssrRenderStyle({ "background": "#c9a84c", "color": "white" })}">${ssrInterpolate(pi + 1)}</span><div class="flex-1 min-w-0"><div dir="rtl" class="mb-1.5"><p class="text-sm font-arabic leading-relaxed" style="${ssrRenderStyle({ "color": "#3a2a1a", "font-family": "'Amiri', 'Traditional Arabic', serif" })}">${ssrInterpolate(para.arabic)}</p></div><div style="${ssrRenderStyle({ "border-top": "1px dashed #e0d5c0" })}" class="mb-1"></div><div><p class="text-[12px] leading-relaxed" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">${ssrInterpolate(para.translation_id)}</p>`);
                      if (para.translation_en) {
                        _push(`<p class="text-[11px] leading-relaxed mt-0.5" style="${ssrRenderStyle({ "color": "#6a8aaa" })}">${ssrInterpolate(para.translation_en)}</p>`);
                      } else {
                        _push(`<!---->`);
                      }
                      _push(`</div></div></div></div>`);
                    });
                    _push(`<!--]--></div>`);
                  } else {
                    _push(`<!---->`);
                  }
                  _push(`</div>`);
                } else {
                  _push(`<!---->`);
                }
                if ((!paragraphsCache.value[page.id] || paragraphsCache.value[page.id].length === 0) && page.translated_id) {
                  _push(`<div class="pt-2 mt-2" style="${ssrRenderStyle({ "border-top": "1px dashed #e0d5c0" })}"><p class="text-[10px] tracking-wider mb-1" style="${ssrRenderStyle({ "color": "#3a7a4d" })}">BAHASA INDONESIA</p><p class="text-sm leading-relaxed" style="${ssrRenderStyle({ "color": "#2a4a3a" })}">${ssrInterpolate(page.translated_id)}</p>`);
                  if (page.translated_en) {
                    _push(`<p class="text-[10px] tracking-wider mt-1" style="${ssrRenderStyle({ "color": "#4a6a8a" })}">ENGLISH</p>`);
                  } else {
                    _push(`<!---->`);
                  }
                  if (page.translated_en) {
                    _push(`<p class="text-xs leading-relaxed" style="${ssrRenderStyle({ "color": "#2a3a4a" })}">${ssrInterpolate(page.translated_en)}</p>`);
                  } else {
                    _push(`<!---->`);
                  }
                  _push(`</div>`);
                } else {
                  _push(`<!---->`);
                }
                _push(`</div>`);
              } else {
                _push(`<!---->`);
              }
              _push(`</div>`);
            });
            _push(`<!--]-->`);
            if (getPages(pdf.id).length === 0) {
              _push(`<div class="mt-2 p-4 text-center text-xs italic" style="${ssrRenderStyle({ "color": "#a0896a" })}">Belum ada halaman.</div>`);
            } else {
              _push(`<!---->`);
            }
            _push(`</div></div>`);
          });
          _push(`<!--]--></div>`);
        } else {
          _push(`<!---->`);
        }
        if (pdfList.value.length === 0) {
          _push(`<div class="rounded-lg p-8 text-center" style="${ssrRenderStyle({ "background": "#faf8f0", "border": "1px dashed #e0d5c0" })}"><div class="text-4xl mb-3" style="${ssrRenderStyle({ "color": "#d4c5a9" })}">\u{1F4C4}</div><p class="text-sm font-medium" style="${ssrRenderStyle({ "color": "#8b7355" })}">Belum ada PDF</p><p class="text-xs mt-1" style="${ssrRenderStyle({ "color": "#a0896a" })}">Upload PDF untuk memulai OCR dan terjemahan</p></div>`);
        } else {
          _push(`<!---->`);
        }
        _push(`</div>`);
      } else {
        _push(`<!---->`);
      }
      _push(`</main><footer class="text-center py-4"><div class="max-w-4xl mx-auto px-4"><div class="flex items-center justify-center gap-2 text-[10px] tracking-wider" style="${ssrRenderStyle({ "color": "#a0896a" })}"><span style="${ssrRenderStyle({ "border-top": "1px solid #d4c5a9", "flex": "1", "max-width": "40px" })}"></span><span>Penerjemah Kitab</span><span style="${ssrRenderStyle({ "border-top": "1px solid #d4c5a9", "flex": "1", "max-width": "40px" })}"></span></div></div></footer></div>`);
    };
  }
});
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("pages/index.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};

export { _sfc_main as default };
//# sourceMappingURL=index-ey9tS652.mjs.map
