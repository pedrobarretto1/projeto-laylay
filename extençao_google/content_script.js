let acaoExecutada = false;
const LAYLAY_PAGE_EXTRACTOR_VERSION = 3;

function sendMessage(message) {
  try { chrome.runtime.sendMessage(message); } catch (_) {}
}

function enviarContexto(tipo, detalhe) {
  sendMessage({
    type: "USER_CONTEXT",
    kind: String(tipo || ""),
    detail: detalhe ?? null,
    url: location.href,
    title: document.title,
    ts: Date.now()
  });
}

function _safeText(v) {
  const s = String(v ?? "").replace(/\s+/g, " ").trim();
  return s.length > 160 ? s.slice(0, 160) : s;
}

function _looksLikePageChrome(text) {
  const value = String(text || "").toLocaleLowerCase("pt-BR");
  if (!value) return true;
  if (/(desculpe incomodar|sorry to interrupt|campanha vai acabar|fundraiser will soon|wikipédia não está à venda|wikipedia is not for sale|tentamos entrar em contato antes|we tried to contact you before)/i.test(value)) {
    return true;
  }
  if (/(pedimos|we ask).{0,160}(por cento|percent).{0,160}(leitores|leitoras|readers).{0,160}(doam|doe|donate)/i.test(value)) {
    return true;
  }
  return /(todas as pessoas|everyone).{0,100}(lendo|reading).{0,140}(doassem|doasse|gave|donated)/i.test(value);
}

function _laylayPageContent() {
  try {
    // Prefere o corpo editorial. ``main`` costuma incluir seletores de idioma,
    // barras e índices (especialmente na Wikipédia), que não são o artigo.
    const chromeSelector = [
      "#centralNotice", "#siteNotice", "#frb-inline", ".centralNotice",
      "[id*='fundraising']", "[class*='fundraising']"
    ].join(", ");
    const preferredSelectors = [
      "[itemprop='articleBody']",
      "#mw-content-text .mw-parser-output",
      "#mw-content-text",
      "article",
      "main",
      "[role='main']",
    ];
    let raiz = null;
    let rootSelector = "body";
    for (const selector of preferredSelectors) {
      const candidate = document.querySelector(selector);
      if (candidate && !candidate.closest(chromeSelector)) {
        raiz = candidate;
        rootSelector = selector;
        break;
      }
    }
    raiz = raiz || document.body;
    if (!raiz) return { success: false, data: {}, error: "A página ainda não possui conteúdo" };
    const clone = raiz.cloneNode(true);
    clone.querySelectorAll(
      "script, style, noscript, svg, canvas, iframe, input, textarea, select, option, " +
      "nav, header, footer, aside, [role='navigation'], [contenteditable='true'], " +
      ".mw-jump-link, .mw-portlet-lang, .vector-page-toolbar, .noprint, " +
      "#centralNotice, #siteNotice, #frb-inline, .centralNotice, " +
      "[id*='fundraising'], [class*='fundraising']"
    )
      .forEach((el) => el.remove());
    const paragraphs = Array.from(clone.querySelectorAll("p"))
      .map((el) => String(el.innerText || el.textContent || "").replace(/\s+/g, " ").trim())
      .filter((text) => text.length >= 80 && !_looksLikePageChrome(text));
    const editorialText = paragraphs.join(" ");
    const rawCandidate = String(clone.innerText || clone.textContent || "").trim();
    const rawContent = editorialText.length >= 200
      ? editorialText
      : (_looksLikePageChrome(rawCandidate) ? "" : rawCandidate);
    const contentSource = editorialText.length >= 200
      ? "paragraphs"
      : (rawContent ? "raw" : "description");
    const content = rawContent
      .replace(/[ \t]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
      .slice(0, 50000);
    const description = String(document.querySelector("meta[name='description']")?.content || "").trim();
    return {
      success: true,
      data: {
        url: window.location.href,
        title: document.title || "",
        description,
        content: content || description,
        extractor_version: LAYLAY_PAGE_EXTRACTOR_VERSION,
        root_selector: rootSelector,
        content_source: contentSource,
        paragraph_count: paragraphs.length,
      },
      error: "",
    };
  } catch (error) {
    return { success: false, data: {}, error: String(error?.message || error || "Falha ao ler a página") };
  }
}

function _isVisibleElement(el) {
  if (!el || !el.isConnected) return false;
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 1 && rect.height > 1;
}

function _findYouTubeSkipButton() {
  const selectors = [
    "button.ytp-ad-skip-button-modern",
    "button.ytp-ad-skip-button",
    "button.ytp-skip-ad-button",
    ".ytp-ad-skip-button-modern button",
    ".ytp-ad-skip-button button",
    ".ytp-skip-ad-button button",
  ];
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (_isVisibleElement(el) && !el.disabled && el.getAttribute?.("aria-disabled") !== "true") {
        return el;
      }
    }
  }

  const adArea = document.querySelector(".video-ads, .ytp-ad-player-overlay, #movie_player.ad-showing");
  if (!adArea) return null;
  return Array.from(adArea.querySelectorAll("button, [role='button']")).find((el) => {
    const label = _elementLabel(el).toLowerCase();
    return _isVisibleElement(el) && /(?:pular|ignorar)\s+an[uú]ncio|skip\s+ads?/.test(label);
  }) || null;
}

function _skipYouTubeAd(timeoutMs = 1600) {
  return new Promise((resolve) => {
    const deadline = Date.now() + timeoutMs;
    const tentar = () => {
      const button = _findYouTubeSkipButton();
      if (button) {
        try {
          button.focus({ preventScroll: true });
          button.click();
          resolve({
            status: "success",
            message: "Anúncio pulado",
            evidence: { label: _elementLabel(button) },
          });
          return;
        } catch (error) {
          resolve({ status: "error", message: String(error?.message || error || "Falha ao clicar") });
          return;
        }
      }
      if (Date.now() < deadline) {
        setTimeout(tentar, 120);
      } else {
        resolve({ status: "not_found", message: "O botão de pular anúncio não está disponível" });
      }
    };
    tentar();
  });
}

function _pageKind() {
  const host = String(location.hostname || "").toLowerCase();
  if (host.includes("youtube.com")) return "youtube";
  if (host.includes("netflix.com")) return "streaming";
  if (document.querySelector("video, audio")) return "media";
  if (document.querySelector("form, input, textarea, [contenteditable='true']")) return "interactive";
  if (document.querySelector("article, main article")) return "article";
  return "general";
}

function _elementLabel(el) {
  if (!el) return "";
  const labelledBy = String(el.getAttribute?.("aria-labelledby") || "").trim();
  const labelledText = labelledBy
    ? labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent || "").join(" ")
    : "";
  return _safeText(
    el.getAttribute?.("aria-label") ||
    labelledText ||
    el.getAttribute?.("placeholder") ||
    el.getAttribute?.("title") ||
    el.innerText ||
    el.textContent ||
    el.getAttribute?.("name") ||
    el.id ||
    ""
  );
}

let _laylayElementCounter = 0;
function _laylayInteractiveElements(limit = 40) {
  const selector = "a[href], button, input, textarea, select, [contenteditable='true'], [role='button'], [role='link'], [role='menuitem'], [role='tab'], [tabindex]";
  const elements = Array.from(document.querySelectorAll(selector));
  const result = [];
  for (const el of elements) {
    if (result.length >= limit || !_isVisibleElement(el)) continue;
    const tag = String(el.tagName || "").toLowerCase();
    const type = String(el.getAttribute?.("type") || "").toLowerCase();
    if (tag === "input" && type === "hidden") continue;
    let elementId = String(el.getAttribute?.("data-laylay-id") || "").trim();
    if (!elementId) {
      _laylayElementCounter += 1;
      elementId = `ll-${_laylayElementCounter}`;
      try { el.setAttribute("data-laylay-id", elementId); } catch (_) {}
    }
    const item = {
      id: elementId,
      tag,
      role: _safeText(el.getAttribute?.("role") || ""),
      label: _elementLabel(el),
      type,
      disabled: Boolean(el.disabled || el.getAttribute?.("aria-disabled") === "true"),
    };
    if (tag === "a") item.href = _safeText(el.href || "");
    // Nunca expõe conteúdo digitado nem o valor de campos sensíveis.
    if (tag === "input" || tag === "textarea" || el.isContentEditable) item.hasValue = Boolean(el.value || el.textContent);
    result.push(item);
  }
  return result;
}

function _laylayPageSnapshot() {
  try {
    const active = document.activeElement;
    const selection = _safeText(window.getSelection?.()?.toString() || "");
    const headings = Array.from(document.querySelectorAll("h1, h2"))
      .filter(_isVisibleElement)
      .map((el) => _safeText(el.textContent || ""))
      .filter(Boolean)
      .slice(0, 12);
    return {
      success: true,
      data: {
        version: 1,
        url: location.href,
        title: document.title || "",
        language: document.documentElement.lang || navigator.language || "",
        kind: _pageKind(),
        loading: document.readyState !== "complete",
        selection,
        focused: active && active !== document.body ? {
          tag: String(active.tagName || "").toLowerCase(),
          label: _elementLabel(active),
          id: String(active.getAttribute?.("data-laylay-id") || ""),
        } : null,
        headings,
        elements: _laylayInteractiveElements(),
        ts: Date.now(),
      },
      error: "",
    };
  } catch (error) {
    return { success: false, data: {}, error: String(error?.message || error || "Falha ao perceber a página") };
  }
}

let _snapshotTimer = null;
function _schedulePageSnapshot(delay = 250) {
  clearTimeout(_snapshotTimer);
  _snapshotTimer = setTimeout(() => {
    const snapshot = _laylayPageSnapshot();
    if (snapshot.success) sendMessage({ type: "PAGE_SNAPSHOT", payload: snapshot.data });
  }, delay);
}

let _lastInteractionTs = Date.now();
let _lastUrl = location.href;
let _idleSent = false;
let _netflixInitDoneForUrl = "";
let _netflixScanRunning = false;

function _markInteraction() {
  _lastInteractionTs = Date.now();
  _idleSent = false;
  _schedulePageSnapshot(350);
}

function _isImportantElement(el) {
  if (!el || typeof el !== "object") return false;
  const tag = String(el.tagName || "").toLowerCase();
  if (tag === "a" || tag === "button" || tag === "input" || tag === "select" || tag === "textarea" || tag === "label") return true;
  const role = String(el.getAttribute?.("role") || "").toLowerCase();
  if (role === "button" || role === "link" || role === "menuitem" || role === "tab") return true;
  const editable = el.isContentEditable === true;
  if (editable) return true;
  const type = String(el.getAttribute?.("type") || "").toLowerCase();
  if (tag === "input" && (type === "text" || type === "search" || type === "email" || type === "password" || type === "url" || type === "number")) return true;
  return false;
}

function _captureClick(e) {
  try {
    const el = e?.target;
    if (!el || typeof el !== "object") return;
    const important = _isImportantElement(el) || _isImportantElement(el.closest?.("a,button,input,select,textarea,[role='button'],[role='link'],[role='menuitem'],[role='tab']"));
    if (!important) return;
    _markInteraction();
    const tag = String(el.tagName || "").toLowerCase();
    const id = _safeText(el.id || "");
    const aria = _safeText(el.getAttribute?.("aria-label") || "");
    const text = _safeText(el.innerText || el.textContent || "");
    const href = _safeText(el.href || el.getAttribute?.("href") || "");
    const label = aria || text || id || tag || "click";
    enviarContexto("click", { label, tag, id, href });
  } catch (_) {}
}

function _emitNav() {
  try {
    if (location.href !== _lastUrl) {
      _lastUrl = location.href;
      _idleSent = false;
    }
    enviarContexto("nav", { url: location.href, title: document.title });
    _schedulePageSnapshot(500);
  } catch (_) {}
}

function _hookHistory() {
  try {
    const origPush = history.pushState;
    const origReplace = history.replaceState;
    history.pushState = function () {
      const r = origPush.apply(this, arguments);
      _emitNav();
      return r;
    };
    history.replaceState = function () {
      const r = origReplace.apply(this, arguments);
      _emitNav();
      return r;
    };
    window.addEventListener("popstate", _emitNav);
    window.addEventListener("hashchange", _emitNav);
  } catch (_) {}
}

function _dispatchKey(key, code, keyCode, extras) {
  try {
    const opts = Object.assign({
      key: key,
      code: code || key,
      keyCode: keyCode || 0,
      which: keyCode || 0,
      bubbles: true,
      cancelable: true,
      composed: true
    }, extras || {});
    const down = new KeyboardEvent("keydown", opts);
    const up = new KeyboardEvent("keyup", opts);
    const target = document.activeElement || document.body || document.documentElement;
    try { target.dispatchEvent(down); } catch (_) {}
    try { document.dispatchEvent(down); } catch (_) {}
    try { target.dispatchEvent(up); } catch (_) {}
    try { document.dispatchEvent(up); } catch (_) {}
  } catch (_) {}
}

function _sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function focar_primeiro_filme() {
  try {
    if (!location.hostname.includes("netflix.com")) return;
    if (!String(location.pathname || "").startsWith("/browse")) return;
    const url = String(location.href || "");
    if (_netflixInitDoneForUrl === url) return;

    for (let i = 0; i < 80; i++) {
      const profilesVisible =
        !!document.querySelector(".profiles-gate-container, [data-uia*='profile'], .profile-icon, .profile-name");
      const cards = document.querySelectorAll(".title-card");
      if (!profilesVisible && cards && cards.length > 0) break;
      await _sleep(100);
    }

    const cards2 = document.querySelectorAll(".title-card");
    if (!cards2 || cards2.length === 0) return;
    _netflixInitDoneForUrl = url;

    if (_netflixScanRunning) return;
    _netflixScanRunning = true;
    try {
      const re = /netflix\.com\/search\?q=.*&jbv=\d+/i;
      for (let i = 0; i < 35; i++) {
        _dispatchKey("Tab", "Tab", 9);
        await _sleep(140);
        const href = String(window.location.href || "");
        if (re.test(href)) {
          await _sleep(200);
          _dispatchKey("Enter", "Enter", 13);
          break;
        }
      }
    } finally {
      _netflixScanRunning = false;
    }
  } catch (_) {}
}


async function scannerNetlifx() {
  try {
    if (!location.hostname.includes("netflix.com")) return;
    const re = /netflix\.com\/search\?q=.*&jbv=\d+/i;
    for (let i = 0; i < 20; i++) {
      _dispatchKey("Tab", "Tab", 9);
      await _sleep(150);
      const href = String(window.location.href || "");
      if (re.test(href)) {
        await _sleep(200);
        _dispatchKey("Enter", "Enter", 13);
        try { sendMessage({ type: "NETFLIX_EVENT", status: "filme_focado", titulo: document.title, url: href }); } catch (_) {}
        try {
          const el = document.documentElement;
          const fn = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen;
          if (typeof fn === "function") {
            try { fn.call(el); } catch (_) {}
          }
          const onClickFS = () => {
            const fn2 = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen;
            if (typeof fn2 === "function") {
              try { fn2.call(el); } catch (_) {}
            }
            document.removeEventListener("click", onClickFS, true);
          };
          document.addEventListener("click", onClickFS, true);
        } catch (_) {}
        break;
      }
    }
  } catch (e) {
    try { console.warn("scannerNetlifx erro:", e); } catch (_) {}
  }
}

async function navegarAteLupa(movie) {
  try {
    try { window.focus(); } catch (_) {}
    const nome = String(movie || "").trim();
    if (!nome) return;
    if (!location.hostname.includes("netflix.com")) return;
    const searchBtn =
      document.querySelector("button.searchTab") ||
      document.querySelector('[aria-label="Busca"]') ||
      document.querySelector('[aria-label="Search"]') ||
      document.querySelector('a[href*="/search"]');
    if (!searchBtn || typeof searchBtn.click !== "function") {
      try { console.error("[LAYLAY] Lupa não encontrada!"); } catch (_) {}
      return;
    }
    try { searchBtn.click(); } catch (_) {}

    let input = null;
    for (let i = 0; i < 30; i++) {
      input = document.querySelector('input[name="searchInput"]') || document.querySelector("input[type='text']");
      if (input) break;
      await _sleep(150);
    }
    if (!input) {
      try { console.error("[LAYLAY] Campo de busca não apareceu!"); } catch (_) {}
      return;
    }
    try { input.focus(); } catch (_) {}
    try { input.value = nome; } catch (_) {}
    try { input.dispatchEvent(new Event("input", { bubbles: true })); } catch (_) {}
    await _sleep(120);
    _dispatchKey("Enter", "Enter", 13);

    for (let i = 0; i < 40; i++) {
      const href = String(window.location.href || "");
      if (href.includes("/search")) break;
      await _sleep(150);
    }
    await _sleep(200);
    await scannerNetlifx();
  } catch (e) {
    try { console.warn("navegarAteLupa erro:", e); } catch (_) {}
  }
}

function _injectConsoleBridge() {
  try {
    const src = `
      (function() {
        if (window.__laylayConsoleHook) return;
        window.__laylayConsoleHook = true;
        function send(level, args) {
          try { window.postMessage({ __laylay_console__: true, level: level, args: args }, "*"); } catch (e) {}
        }
        var origLog = console.log;
        var origErr = console.error;
        console.log = function() { try { send("log", Array.prototype.slice.call(arguments)); } catch (e) {} return origLog.apply(console, arguments); };
        console.error = function() { try { send("error", Array.prototype.slice.call(arguments)); } catch (e) {} return origErr.apply(console, arguments); };
        window.addEventListener("error", function(ev) {
          try { send("error", [String(ev && ev.message || "error"), String(ev && ev.filename || ""), String(ev && ev.lineno || ""), String(ev && ev.colno || "")]); } catch (e) {}
        });
        window.addEventListener("unhandledrejection", function(ev) {
          try { send("error", ["unhandledrejection", String(ev && ev.reason || "")]); } catch (e) {}
        });
      })();
    `;
    const s = document.createElement("script");
    s.textContent = src;
    (document.documentElement || document.head || document.body).appendChild(s);
    s.remove();
  } catch (_) {}
}

// ====================== SUPER PODERES LAYLAY (DOM Manipulation) ======================

// Busca campos de input de busca/texto na página
function _findSearchInput() {
    // Ordem de prioridade: input de busca explícito → genérico de texto → qualquer input
    const searchSelectors = [
        'input[type="search"]',
        'input[placeholder*="busca" i]',
        'input[placeholder*="pesquisa" i]',
        'input[placeholder*="search" i]',
        'input[placeholder*="o que" i]',
        'input[name="q"]',
        'input[name="query"]',
        'input[name="busca"]',
        'input[role="searchbox"]',
        '[role="searchbox"]',
        '[role="combobox"]',
        'input[type="text"]',
    ];
    for (const sel of searchSelectors) {
        const el = document.querySelector(sel);
        if (el && el.offsetParent !== null) return el;
    }
    return null;
}

// Digita em um input de forma que frameworks React/Vue/Angular detectem
function _typeInElement(el, text) {
    if (!el) return false;
    try {
        // Foca primeiro
        el.focus();
        el.click();
        
        // Limpa o campo existente
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        if (nativeInputValueSetter) {
            nativeInputValueSetter.call(el, text);
        } else {
            el.value = text;
        }
        
        // Dispara os eventos que frameworks modernos esperam
        el.dispatchEvent(new Event('input',   { bubbles: true, composed: true }));
        el.dispatchEvent(new Event('change',  { bubbles: true, composed: true }));
        el.dispatchEvent(new KeyboardEvent('keydown', { key: text.slice(-1), bubbles: true }));
        el.dispatchEvent(new KeyboardEvent('keyup',   { key: text.slice(-1), bubbles: true }));
        return true;
    } catch(e) {
        return false;
    }
}

function _findClickableByText(text) {
    const lowerText = text.toLowerCase().trim();
    // Inclui inputs para achar campos de busca pelo placeholder
    const selectors = 'a, button, [role="button"], [role="link"], span, div, label, input[type="button"], input[type="submit"], input[type="search"], input[type="text"]';
    const elements = Array.from(document.querySelectorAll(selectors));
    
    // 1. Tenta match exato por texto/placeholder
    let found = elements.find(el => {
        const content = (el.innerText || el.textContent || el.placeholder || "").toLowerCase().trim();
        return content === lowerText && el.offsetParent !== null;
    });
    
    // 2. Tenta match parcial (contém o texto)
    if (!found) {
        found = elements.find(el => {
            const content = (el.innerText || el.textContent || el.placeholder || "").toLowerCase().trim();
            return content.includes(lowerText) && el.offsetParent !== null;
        });
    }
    
    return found;
}

function _normalizeGoogleSearchText(text) {
    return String(text || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9\s]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function _tokenizeGoogleSearchText(text) {
    const stop = new Set([
        "a", "o", "os", "as", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
        "pra", "pro", "para", "por", "com", "sem", "um", "uma", "uns", "umas", "que"
    ]);
    return _normalizeGoogleSearchText(text)
        .split(" ")
        .filter((part) => part && part.length >= 2 && !stop.has(part));
}

function _getGoogleUrlParts(href) {
    try {
        const u = new URL(String(href || ""));
        return {
            host: String(u.hostname || "").toLowerCase().replace(/^www\./, ""),
            path: String(u.pathname || "").toLowerCase(),
            search: String(u.search || "").toLowerCase(),
        };
    } catch (_) {
        return { host: "", path: "", search: "" };
    }
}

function _scoreGoogleCandidate(query, title, snippet, href) {
    const q = _normalizeGoogleSearchText(query);
    const t = _normalizeGoogleSearchText(title);
    const s = _normalizeGoogleSearchText(snippet);
    const h = _normalizeGoogleSearchText(href);
    const qTokens = _tokenizeGoogleSearchText(query);
    const urlParts = _getGoogleUrlParts(href);
    const host = _normalizeGoogleSearchText(urlParts.host);
    const path = _normalizeGoogleSearchText(urlParts.path);
    let score = 0;

    if (!qTokens.length) return 0;

    if (t === q) score += 120;
    if (t.includes(q) || q.includes(t)) score += 45;
    if (s.includes(q)) score += 15;

    const overlapTokens = [];
    for (const token of qTokens) {
        if (t.includes(token)) score += 12;
        if (s.includes(token)) score += 5;
        if (h.includes(token)) score += 3;
        if (host.includes(token)) score += 6;
        if (path.includes(token)) score += 2;
        if (t.includes(token) || s.includes(token)) overlapTokens.push(token);
    }

    const overlap = overlapTokens.length;
    score += overlap * 8;

    if (/youtube|youtu\.be/.test(h)) score += 8;
    if (/spotify|deezer|soundcloud|music|m\.youtube|youtube\.com\/watch/.test(h)) score += 6;
    if (/lyrics|letra|tradu[cç][aã]o|live|ao vivo|remix|cover/.test(t) && qTokens.length <= 4) score -= 10;

    const wantsMusic = /(\bmusica\b|\bmusica\b|\bmusic\b|\bplaylist\b|\byoutube\b|\bspotify\b|\blyrics\b|\bletra\b|\bclipe\b|\bvideo\b|\bvideo oficial\b)/.test(q);
    const wantsSite = /(\bsite\b|\babrir\b|\babre\b|\bentra\b|\bentrar\b|\blogin\b|\bacessar\b)/.test(q);
    if (wantsMusic && /youtube|youtu\.be|music\.youtube|spotify|deezer|soundcloud/.test(h)) score += 14;

    const hostBase = host.split(".")[0] || "";
    if (hostBase && qTokens.includes(hostBase) && hostBase.length > 2) score += 22;
    if (wantsSite && hostBase && qTokens.includes(hostBase)) score += 10;
    if (wantsSite && /(home|inicio|start|main|index)$/.test(path)) score += 6;

    if (host && qTokens.length >= 2 && qTokens.every((token) => host.includes(token))) score += 18;

    if (/google\.(com|com\.br)$/.test(host) || /support\.google|accounts\.google/.test(host)) score -= 25;
    if (/\/search\b/.test(path) || /\/url\b/.test(path)) score -= 18;
    if (/adservice|doubleclick|aclk|adurl=/.test(h)) score -= 100;

    return score;
}

function _extractGoogleResultCandidates() {
    const anchors = Array.from(document.querySelectorAll('div#search a[href], #search a[href]'));
    const candidates = [];
    for (const a of anchors) {
        if (!a || typeof a.href !== "string") continue;
        const href = a.href;
        if (!href) continue;
        if (/google\./i.test(href) && !/https?:\/\/[^/]*google\.[^/]+\/url/i.test(href)) continue;
        if (/googleadservices|aclk=|adurl=|\/search\?/i.test(href)) continue;
        const h3 = a.querySelector("h3");
        const title = String(h3?.textContent || a.textContent || "").replace(/\s+/g, " ").trim();
        if (!title) continue;
        const snippetNode = a.closest("div.g, div.MjjYud, div.tF2Cxc, div.Ww4FFb, div[data-ved]") || a.parentElement;
        const snippet = String(snippetNode?.innerText || "").replace(/\s+/g, " ").trim();
        candidates.push({ href, title, snippet });
    }
    return candidates;
}

function _resolveBestGoogleResult(query) {
    const candidates = _extractGoogleResultCandidates();
    if (!candidates.length) return null;

    const ranked = candidates
        .map((item) => ({
            ...item,
            score: _scoreGoogleCandidate(query, item.title, item.snippet, item.href)
        }))
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score);

    return ranked[0] || null;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    try {
        const payload = request.payload || request;

        if (request.action === "GET_PAGE_CONTENT") {
            sendResponse(_laylayPageContent());
            return;
        }

        if (request.action === "GET_PAGE_SNAPSHOT") {
            sendResponse(_laylayPageSnapshot());
            return;
        }
        
        if (request.action === "click") {
            let selector = payload.selector || "";
            let el = null;

            const elementId = String(payload.element_id || payload.elementId || "").trim();
            if (elementId) {
                try { el = document.querySelector(`[data-laylay-id="${CSS.escape(elementId)}"]`); } catch (_) {}
            }

            // 🛡️ PROTEÇÃO ANTI-ALUCINAÇÃO: Fallback para :contains("Texto")
            const containsMatch = selector.match(/:contains\(['"](.+?)['"]\)/i);
            if (!el && containsMatch) {
                const textToFind = containsMatch[1].toLowerCase().trim();
                console.log(`🔍 Buscando elemento por texto (:contains): ${textToFind}`);
                el = _findClickableByText(textToFind);
            } else {
                // 1. Tenta pelo seletor CSS normal
                if (!el && selector && (selector.includes('[') || selector.includes('.') || selector.includes('#'))) {
                    try { el = document.querySelector(selector); } catch(e) {}
                }
                // 2. Fallback: Busca por texto simples
                if (!el && selector) {
                    el = _findClickableByText(selector);
                }
            }

            if (el && _isVisibleElement(el) && !el.disabled && el.getAttribute?.("aria-disabled") !== "true") {
                el.focus();
                el.click();
                el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                console.log(`🤖 Laylay clicou em: ${selector || el.textContent}`);
                if (sendResponse) sendResponse({ status: "success", evidence: { elementId: el.getAttribute?.("data-laylay-id") || "", label: _elementLabel(el) } });
            } else {
                console.warn(`⚠️ Laylay não achou o elemento: ${selector}`);
                if (sendResponse) sendResponse({ status: "error", message: "Element not found" });
            }
        }
        else if (request.action === "press") {
            const key = payload.key || "enter";
            let keyCode = 13;
            if (key.toLowerCase() === "enter") keyCode = 13;
            else if (key.toLowerCase() === "escape") keyCode = 27;
            else if (key.toLowerCase() === "tab") keyCode = 9;
            else if (key.toLowerCase() === "space") keyCode = 32;
            
            // Dispara no elemento focado E no document para garantir
            const target = document.activeElement || document.body;
            const opts = { key, code: key, keyCode, which: keyCode, bubbles: true, cancelable: true };
            try { target.dispatchEvent(new KeyboardEvent("keydown", opts)); } catch(_) {}
            try { document.dispatchEvent(new KeyboardEvent("keydown", opts)); } catch(_) {}
            try { target.dispatchEvent(new KeyboardEvent("keyup",   opts)); } catch(_) {}
            console.log(`🤖 Laylay apertou a tecla: ${key}`);
            if (sendResponse) sendResponse({ status: "success" });
        }
        else if (request.action === "type") {
            let el = null;
            // Tenta seletor direto primeiro
            if (payload.selector) {
                try { el = document.querySelector(payload.selector); } catch(_) {}
            }
            // Se não achou pelo seletor, tenta achar a barra de busca da página
            if (!el) el = _findSearchInput();
            
            if (el) {
                const fieldSignals = `${el.type || ""} ${el.name || ""} ${el.id || ""} ${el.autocomplete || ""} ${el.placeholder || ""}`.toLowerCase();
                const sensitiveField = ["password", "senha", "cc-number", "credit-card", "cartao", "cartão", "cvv", "cvc"].some((marker) => fieldSignals.includes(marker));
                if (sensitiveField) {
                    console.warn("🛑 Digitação da Laylay bloqueada em campo sensível");
                    if (sendResponse) sendResponse({ status: "sensitive_page", message: "Sensitive input blocked" });
                    return true;
                }
                const typed = _typeInElement(el, payload.text || "");
                console.log(`🤖 Laylay digitou "${payload.text}" em: ${el.tagName} (${el.type || el.role || "?"})`);
                if (sendResponse) sendResponse({ status: typed ? "success" : "partial" });
            } else {
                console.warn(`⚠️ Laylay não achou campo para digitar`);
                if (sendResponse) sendResponse({ status: "error", message: "Input not found" });
            }
        }
        else if (request.action === "search_in_page") {
            // ─── NOVA AÇÃO: Clica no gatilho de busca → digita → Enter ───
            const query = payload.query || payload.text || "";
            console.log(`🔍 Laylay executando busca na página: "${query}"`);

            async function doSearch() {
                // PASSO 1: Tenta clicar em qualquer botão/ícone de busca que abre o input
                const triggerSelectors = [
                    '[data-testid*="search" i]',
                    '[aria-label*="busca" i]',
                    '[aria-label*="pesquis" i]',
                    '[aria-label*="search" i]',
                    '[placeholder*="busca" i]',
                    '[placeholder*="pesquis" i]',
                    'button[class*="search" i]',
                    'a[href*="search" i]',
                    '.search-bar', '.searchbar', '.search-input',
                ];
                let triggered = false;
                for (const sel of triggerSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.tagName !== 'INPUT' && el.offsetParent) {
                        try { el.click(); triggered = true; console.log(`🖱️ Clicou no trigger: ${sel}`); break; } catch(_) {}
                    }
                }
                if (triggered) await new Promise(r => setTimeout(r, 600));

                // PASSO 2: Achar o input
                let input = _findSearchInput();
                if (!input) {
                    // Qualquer input visível como fallback
                    const allInputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null);
                    input = allInputs[0] || null;
                }

                if (!input) {
                    console.warn(`⚠️ Nenhuma barra de busca encontrada na página`);
                    throw new Error("Nenhuma barra de busca encontrada na página");
                }
                console.log(`✏️ Input encontrado: ${input.tagName} type="${input.type}" placeholder="${input.placeholder}"`);

                // PASSO 3: Digitar usando setter nativo (compatível com React/Vue)
                input.focus();
                input.click();
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                if (nativeSetter) {
                    nativeSetter.call(input, query);
                } else {
                    input.value = query;
                }
                input.dispatchEvent(new Event('input',  { bubbles: true, composed: true }));
                input.dispatchEvent(new Event('change', { bubbles: true, composed: true }));

                // PASSO 4: Aguarda o React processar e pressiona Enter / clica Submit
                await new Promise(r => setTimeout(r, 400));
                const enterOpts = { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true };
                input.dispatchEvent(new KeyboardEvent("keydown", enterOpts));
                input.dispatchEvent(new KeyboardEvent("keyup",   enterOpts));
                // Tenta também submeter o form pai
                const form = input.closest('form');
                if (form) {
                    try { form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); } catch(_) {}
                    try { form.requestSubmit(); } catch(_) {}
                }
                // Tenta clicar botão submit explícito
                const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn && submitBtn.offsetParent) submitBtn.click();

                console.log(`✅ Laylay buscou: "${query}"`);
            }

            doSearch().then(() => {
                if (sendResponse) sendResponse({ status: "success", evidence: { query } });
            }).catch((error) => {
                if (sendResponse) sendResponse({ status: "error", message: String(error?.message || error || "Search failed") });
            });
        }
        else if (request.action === "scroll") {
            const direction = payload.direction || "down";
            const amount = payload.amount || 400;
            window.scrollBy({ top: direction === "down" ? amount : -amount, behavior: 'smooth' });
            if (sendResponse) sendResponse({ status: "success" });
        }
        else if (request.action === "youtube_control") {
            const video = document.querySelector('video');
            const cmd = String(payload.command || request.command || "").toLowerCase();
            if (cmd === "queue_select") {
                const requestedId = String(
                    payload.queue_item_id || request.queue_item_id || ""
                ).trim();
                const requestedIndex = Number(
                    payload.queue_index ?? request.queue_index
                );
                const queueRoot = document.querySelector(
                    "ytd-playlist-panel-renderer, ytmusic-player-queue, #playlist-items"
                );
                const rows = queueRoot ? Array.from(queueRoot.querySelectorAll(
                    "ytd-playlist-panel-video-renderer, ytmusic-player-queue-item"
                )) : [];
                const selected = rows.findIndex((row) => (
                    row.hasAttribute("selected") ||
                    row.getAttribute("aria-selected") === "true" ||
                    row.classList.contains("selected")
                ));
                const upcoming = rows.slice(selected >= 0 ? selected + 1 : 0);
                const row = Number.isInteger(requestedIndex)
                    ? upcoming[requestedIndex] : null;
                const anchor = row?.querySelector(
                    "a#wc-endpoint, a[href*='/watch'], a[href*='/shorts/']"
                );
                let observedId = "";
                try {
                    const parsed = new URL(
                        String(anchor?.href || anchor?.getAttribute("href") || ""),
                        location.href,
                    );
                    const parts = parsed.pathname.split("/").filter(Boolean);
                    observedId = String(
                        parsed.searchParams.get("v") ||
                        (["shorts", "embed", "live"].includes(parts[0])
                            ? parts[1] : "") || ""
                    );
                } catch (_) {}
                if (
                    !/^[A-Za-z0-9_-]{11}$/.test(requestedId) || !row ||
                    !anchor || observedId !== requestedId
                ) {
                    if (sendResponse) sendResponse({
                        status: "stale_context",
                        message: "A fila mudou antes da seleção da faixa",
                        evidence: {
                            queueIndex: Number.isInteger(requestedIndex)
                                ? requestedIndex : null,
                            requestedId,
                            observedId,
                        },
                    });
                } else {
                    const beforeId = (() => {
                        try {
                            return String(new URL(location.href).searchParams.get("v") || "");
                        } catch (_) { return ""; }
                    })();
                    anchor.click();
                    const startedAt = Date.now();
                    const verifySelection = () => {
                        let currentId = "";
                        try {
                            currentId = String(
                                new URL(location.href).searchParams.get("v") || ""
                            );
                        } catch (_) {}
                        const selectedNow = Boolean(
                            row.isConnected && (
                                row.hasAttribute("selected") ||
                                row.getAttribute("aria-selected") === "true" ||
                                row.classList.contains("selected")
                            )
                        );
                        const confirmed = currentId === requestedId || selectedNow;
                        if (confirmed || Date.now() - startedAt >= 3500) {
                            if (sendResponse) sendResponse({
                                status: confirmed ? "success" : "state_not_changed",
                                message: confirmed ? "" : "O player não confirmou a faixa escolhida",
                                evidence: {
                                    beforeId, currentId, requestedId,
                                    queueIndex: requestedIndex,
                                    changed: confirmed,
                                },
                            });
                            return;
                        }
                        setTimeout(verifySelection, 120);
                    };
                    setTimeout(verifySelection, 120);
                }
            }
            else if (cmd === "skip_ad") {
                // Executado somente após um pedido explícito recebido do Python.
                // Não há observador nem clique automático em anúncios futuros.
                _skipYouTubeAd().then((result) => {
                    if (sendResponse) sendResponse(result);
                });
            }
            else if (cmd === "pause" || cmd === "play" || cmd === "pause_play") {
                const controlAndVerify = async () => {
                    const waitFor = async (predicate, timeoutMs, intervalMs = 150) => {
                        const startedAt = Date.now();
                        let value = predicate();
                        while (!value && Date.now() - startedAt < timeoutMs) {
                            await new Promise((resolve) => setTimeout(resolve, intervalMs));
                            value = predicate();
                        }
                        return value;
                    };
                    let currentVideo = video || await waitFor(
                        () => document.querySelector('video'), 3500
                    );
                    const shouldPause = cmd === "pause" || (
                        cmd === "pause_play" && currentVideo && !currentVideo.paused
                    );
                    if (shouldPause) {
                        try {
                            if (currentVideo) currentVideo.pause();
                            else {
                                const playBtn = document.querySelector('.ytp-play-button');
                                if (playBtn) playBtn.click();
                                else _dispatchKey("k", "KeyK", 75);
                            }
                            currentVideo = currentVideo || await waitFor(
                                () => document.querySelector('video'), 1800
                            );
                            const pausedConfirmed = Boolean(currentVideo && await waitFor(
                                () => currentVideo.paused, 1800
                            ));
                            if (sendResponse) sendResponse({
                                status: pausedConfirmed ? "success" : "state_not_changed",
                                message: pausedConfirmed ? "" : "O player não confirmou a pausa",
                                evidence: {
                                    playing: Boolean(currentVideo && !currentVideo.paused),
                                    paused: Boolean(currentVideo && currentVideo.paused),
                                },
                            });
                        } catch (error) {
                            if (sendResponse) sendResponse({
                                status: "error",
                                message: String(error?.message || error || "Falha ao pausar o player"),
                                evidence: { paused: false },
                            });
                        }
                        return;
                    }
                    let failureMessage = "";
                    let attempts = 0;
                    try {
                        if (currentVideo) {
                            if (shouldPause) currentVideo.pause();
                            else {
                                attempts += 1;
                                try {
                                    await currentVideo.play();
                                } catch (error) {
                                    failureMessage = String(
                                        error?.message || error || "O player recusou o primeiro play"
                                    );
                                }
                            }
                        } else {
                            const playBtn = document.querySelector('.ytp-play-button');
                            attempts += 1;
                            if (playBtn) playBtn.click();
                            else _dispatchKey("k", "KeyK", 75);
                        }
                        currentVideo = await waitFor(
                            () => document.querySelector('video'), 2500
                        );
                        let playing = Boolean(currentVideo && await waitFor(
                            () => !currentVideo.paused && !currentVideo.ended, 2200
                        ));
                        // Alguns players recusam video.play() sem gesto, mas aceitam
                        // o clique no próprio controle. Fazemos uma única tentativa
                        // observável e só então classificamos como autoplay bloqueado.
                        if (!shouldPause && !playing) {
                            const playBtn = document.querySelector('.ytp-play-button');
                            attempts += 1;
                            if (playBtn) playBtn.click();
                            else if (currentVideo) {
                                try { await currentVideo.play(); }
                                catch (error) {
                                    failureMessage = String(
                                        error?.message || error || failureMessage
                                    );
                                }
                            }
                            currentVideo = await waitFor(
                                () => document.querySelector('video'), 1500
                            );
                            playing = Boolean(currentVideo && await waitFor(
                                () => !currentVideo.paused && !currentVideo.ended, 2500
                            ));
                        }
                        // O YouTube pode iniciar o elemento ainda sem dados suficientes.
                        // Esperamos um estado reproduzível antes de confirmar o efeito.
                        if (!shouldPause && playing && currentVideo.readyState < 2) {
                            await waitFor(
                                () => currentVideo.readyState >= 2, 1800
                            );
                        }
                        const paused = Boolean(currentVideo && currentVideo.paused);
                        const muted = Boolean(currentVideo && currentVideo.muted);
                        const volume = currentVideo ? Number(currentVideo.volume) : 0;
                        const readyState = currentVideo ? Number(currentVideo.readyState) : 0;
                        const audible = Boolean(playing && !muted && volume > 0 && readyState >= 2);
                        const verified = shouldPause ? paused : audible;
                        if (sendResponse) sendResponse({
                            status: verified ? "success" : (
                                playing ? "playing_muted" : "autoplay_blocked"
                            ),
                            message: verified ? "" : (
                                playing
                                    ? "O vídeo iniciou, mas o áudio está mudo ou sem volume"
                                    : (failureMessage || "O navegador não permitiu iniciar o player")
                            ),
                            evidence: {
                                playing, paused, audible, muted, volume,
                                readyState, attempts,
                            },
                        });
                    } catch (error) {
                        if (sendResponse) sendResponse({
                            status: "autoplay_blocked",
                            message: String(error?.message || error || "Falha ao controlar o player"),
                            evidence: { playing: false },
                        });
                    }
                };
                void controlAndVerify();
            }
            else if (cmd === "next") {
                const beforeUrl = window.location.href;
                const beforeTitle = document.title;
                const beforeVideoId = new URL(beforeUrl).searchParams.get("v") || "";
                const nextBtn = document.querySelector('.ytp-next-button');
                if (nextBtn) nextBtn.click();
                else _dispatchKey("N", "KeyN", 78, { shiftKey: true });
                const startedAt = Date.now();
                const verifyNext = () => {
                    const afterUrl = window.location.href;
                    const afterTitle = document.title;
                    const afterVideoId = new URL(afterUrl).searchParams.get("v") || "";
                    const changed = Boolean(
                        (afterVideoId && afterVideoId !== beforeVideoId)
                        || afterUrl !== beforeUrl
                        || afterTitle !== beforeTitle
                    );
                    if (changed || Date.now() - startedAt >= 2800) {
                        if (sendResponse) sendResponse({
                            status: changed ? "success" : "state_not_changed",
                            message: changed ? "" : "A faixa não mudou após o comando",
                            evidence: {
                                beforeUrl, afterUrl, beforeVideoId, afterVideoId,
                                beforeTitle, afterTitle, changed,
                            },
                        });
                        return;
                    }
                    setTimeout(verifyNext, 120);
                };
                setTimeout(verifyNext, 120);
            }
            else if (cmd === "prev") {
                const beforeUrl = window.location.href;
                const beforeTitle = document.title;
                const beforeVideoId = new URL(beforeUrl).searchParams.get("v") || "";
                const prevBtn = document.querySelector('.ytp-prev-button');
                if (prevBtn) prevBtn.click();
                else _dispatchKey("P", "KeyP", 80, { shiftKey: true });
                const startedAt = Date.now();
                const verifyPrev = () => {
                    const currentUrl = window.location.href;
                    const currentTitle = document.title;
                    const currentVideoId = new URL(currentUrl).searchParams.get("v") || "";
                    const sameVideo = currentVideoId === beforeVideoId;
                    const changed = Boolean(
                        (currentVideoId && !sameVideo)
                        || currentUrl !== beforeUrl
                        || currentTitle !== beforeTitle
                    );
                    if (changed || Date.now() - startedAt >= 2800) {
                        if (sendResponse) sendResponse({
                            status: changed ? "success" : "state_not_changed",
                            message: changed ? "" : "A faixa anterior não foi observada",
                            evidence: {
                                beforeUrl, currentUrl, beforeVideoId, currentVideoId,
                                beforeTitle, currentTitle, changed,
                            },
                        });
                        return;
                    }
                    setTimeout(verifyPrev, 120);
                };
                setTimeout(verifyPrev, 120);
            }
            else if (cmd === "replay") {
                if (video) video.currentTime = 0;
                else {
                    const prevBtn = document.querySelector('.ytp-prev-button');
                    if (prevBtn) prevBtn.click();
                    else _dispatchKey("P", "KeyP", 80, { shiftKey: true });
                }
                setTimeout(() => {
                    const videoNow = document.querySelector('video');
                    const currentTime = Number(videoNow?.currentTime || 0);
                    const restarted = Boolean(videoNow && currentTime <= 2.5);
                    if (sendResponse) sendResponse({
                        status: restarted ? "success" : "state_not_changed",
                        message: restarted ? "" : "O reinício da faixa não foi observado",
                        evidence: {
                            currentTime,
                            restarted,
                            url: window.location.href,
                            title: document.title,
                        },
                    });
                }, 350);
            }
            else if (cmd === "repeat_toggle") {
                const videoNow = video || document.querySelector('video');
                if (!videoNow) {
                    if (sendResponse) sendResponse({
                        status: "player_unavailable",
                        message: "Nenhum player foi encontrado para alterar a repetição",
                        evidence: { repeatEnabled: false },
                    });
                } else {
                    videoNow.loop = !videoNow.loop;
                    if (sendResponse) sendResponse({
                        status: "success",
                        evidence: { repeatEnabled: !!videoNow.loop },
                    });
                    try { _emitLaylayPlayerState(videoNow, true); } catch (_) {}
                }
            }
        }
    } catch (error) {
        console.error("❌ Erro na automação:", error);
        if (sendResponse) sendResponse({ status: "error", message: String(error?.message || error || "Erro na automação") });
    }
    return true;
});

window.addEventListener("load", () => _schedulePageSnapshot(300), { once: true });
document.addEventListener("focusin", () => _schedulePageSnapshot(250), true);
_schedulePageSnapshot(700);

function _listenConsoleBridge() {
  try {
    window.addEventListener("message", (ev) => {
      const d = ev?.data;
      if (!d || d.__laylay_console__ !== true) return;
      const level = String(d.level || "log");
      const args = Array.isArray(d.args) ? d.args : [d.args];
      const msg = _safeText(args.map((a) => {
        try { return typeof a === "string" ? a : JSON.stringify(a); } catch (_) { return String(a); }
      }).join(" "));
      enviarContexto("console", { level, message: msg });
    });
  } catch (_) {}
}

function onceYouTubeResults() {
  if (!location.pathname.startsWith("/results") || acaoExecutada) return;
  const observer = new MutationObserver(() => {
    if (acaoExecutada) return;
    const a =
      document.querySelector('ytd-video-renderer a#thumbnail[href*="/watch"]') ||
      document.querySelector('a#video-title-link[href*="/watch"]') ||
      document.querySelector('ytd-video-renderer a#video-title[href*="/watch"]');
    if (a && a.href) {
      acaoExecutada = true;
      observer.disconnect();
      try { a.click(); } catch (_) {} // Clique natural respeita a SPA do YouTube e evita reloads bizarros
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
}

function onceYouTubeWatch() {
    // Reduzido para não interagir com o fluxo autoplay do YouTube (que causa mute/freeze bugs)
    return;
}

if (location.hostname.includes("youtube.com")) {
  onceYouTubeResults();
  onceYouTubeWatch();
}


window.addEventListener("load", () => {
  sendMessage({ action: "title_update", title: document.title });
  _emitNav();
});

const titleNode = document.querySelector("head > title");
if (titleNode) {
  const titleObserver = new MutationObserver(() => {
    sendMessage({ action: "title_update", title: document.title });
    _emitNav();
  });
  titleObserver.observe(titleNode, { childList: true });
}

let __laylayAutoClickRunning = false;
function _laylayAutoClickEnabledFromUrl() {
  try {
    const host = String(location.hostname || "");
    if (!host.includes("google.")) return false;
    const sp = new URLSearchParams(String(location.search || ""));
    return String(window.location.search || "").includes("laylay_auto=true");
  } catch (_) {
    return false;
  }
}

function clicarPrimeiroResultado() {
  if (__laylayAutoClickRunning) return;
  if (!_laylayAutoClickEnabledFromUrl()) return;
  __laylayAutoClickRunning = true;

  const reAd = /(Patrocinado|Anúncio|Anuncio)/i;

  const hasAdTextUp = (node) => {
    let cur = node;
    for (let i = 0; i < 8 && cur; i++) {
      const txt = String(cur.textContent || "");
      if (reAd.test(txt)) return true;
      cur = cur.parentElement;
    }
    return false;
  };

  const getQueryFromUrl = () => {
    try {
      const sp = new URLSearchParams(String(location.search || ""));
      return String(sp.get("q") || sp.get("as_q") || sp.get("oq") || sp.get("query") || "").trim();
    } catch (_) {
      return "";
    }
  };

  const tryFindAndReplace = () => {
    if (!String(window.location.search || "").includes("laylay_auto=true")) return false;
    const query = getQueryFromUrl();
    const best = _resolveBestGoogleResult(query);
    if (best && best.href) {
      const link = Array.from(document.querySelectorAll("a[href]")).find((a) => a && a.href === best.href) || null;
      if (!link || hasAdTextUp(link)) return false;
      try { enviarContexto("auto_click", { href: best.href, title: _safeText(best.title), score: best.score, query }); } catch (_) {}
      try { window.location.replace(best.href); } catch (_) { try { window.location.href = best.href; } catch (_) {} }
      return true;
    }

    const h3s = document.querySelectorAll("div#search a h3");
    for (const h3 of h3s) {
      const p = h3?.parentElement;
      const link = (p && String(p.tagName || "").toUpperCase() === "A") ? p : (h3?.closest ? h3.closest("a") : null);
      const href = link && link.href ? String(link.href) : "";
      if (!href) continue;
      if (href.includes("googleadservices") || href.includes("aclk") || href.includes("adurl=")) continue;
      if (hasAdTextUp(link)) continue;
      try { enviarContexto("auto_click", { href, title: _safeText(h3.textContent || ""), query, fallback: true }); } catch (_) {}
      try { window.location.replace(href); } catch (_) { try { window.location.href = href; } catch (_) {} }
      return true;
    }
    return false;
  };

  const fail = () => {
    __laylayAutoClickRunning = false;
    try { sendMessage({ action: "auto_click_status", status: "erro_clique", motivo: "Link não encontrado" }); } catch (_) {}
  };

  const start = () => {
    let tries = 0;
    const t = setInterval(() => {
      tries += 1;
      if (tryFindAndReplace()) {
        clearInterval(t);
        try { obs.disconnect(); } catch (_) {}
        return;
      }
      if (tries >= 10) {
        clearInterval(t);
        try { obs.disconnect(); } catch (_) {}
        fail();
      }
    }, 200);
  };

  const obs = new MutationObserver(() => {
    try { if (tryFindAndReplace()) obs.disconnect(); } catch (_) {}
  });
  try { obs.observe(document.documentElement, { childList: true, subtree: true }); } catch (_) {}

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
}

try {
  if (_laylayAutoClickEnabledFromUrl()) {
    clicarPrimeiroResultado();
  }
} catch (_) {}

function _laylayYoutubeChannelText(node) {
  const normalize = (value) => String(value || "").replace(/\s+/g, " ").trim();
  if (!node) return "";
  const specific = [
    node.matches?.("#text, a, yt-formatted-string") ? node : null,
    node.querySelector?.("#text"),
    node.querySelector?.(
      "a[href*='/@'], a[href*='/channel/'], a[href*='/c/'], a[href*='/user/']",
    ),
    node.querySelector?.("yt-formatted-string"),
  ];
  for (const candidate of specific) {
    const text = normalize(candidate?.textContent);
    if (text) return text;
  }
  return normalize(node.textContent);
}

function _laylayYoutubeQueueSnapshot() {
  try {
    const root = document.querySelector(
      "ytd-playlist-panel-renderer, ytmusic-player-queue, #playlist-items",
    );
    if (!root) return { observed: false, items: [] };
    const rows = Array.from(root.querySelectorAll(
      "ytd-playlist-panel-video-renderer, ytmusic-player-queue-item",
    ));
    const selected = rows.findIndex((row) => (
      row.hasAttribute("selected") || row.getAttribute("aria-selected") === "true" ||
      row.classList.contains("selected")
    ));
    const start = selected >= 0 ? selected + 1 : 0;
    const items = rows.slice(start, start + 8).map((row) => {
      const anchor = row.querySelector("a#wc-endpoint, a[href*='/watch'], a[href*='/shorts/']");
      const titleNode = row.querySelector("#video-title, .song-title, yt-formatted-string.title");
      const channelNode = row.querySelector("#byline, .byline, .subtitle, #channel-name");
      const durationNode = row.querySelector("#text, .badge-shape-wiz__text, .duration");
      const href = String(anchor?.href || anchor?.getAttribute("href") || "");
      let videoId = "";
      try {
        const parsed = new URL(href, location.href);
        const parts = parsed.pathname.split("/").filter(Boolean);
        videoId = String(
          parsed.searchParams.get("v") ||
          (["shorts", "embed", "live"].includes(parts[0]) ? parts[1] : "") || ""
        );
      } catch (_) {}
      const durationText = String(durationNode?.textContent || "").replace(/\s+/g, " ").trim();
      const durationParts = durationText.split(":").map((part) => Number(part));
      const durationSeconds = durationParts.every(Number.isFinite)
        ? durationParts.reduce((total, value) => total * 60 + value, 0) : 0;
      return {
        title: String(titleNode?.textContent || anchor?.textContent || "").replace(/\s+/g, " ").trim(),
        channel: _laylayYoutubeChannelText(channelNode),
        videoId,
        durationSeconds,
      };
    }).filter((item) => item.title);
    return { observed: true, items };
  } catch (_) {
    return { observed: false, items: [] };
  }
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  console.log("Comando recebido na página:", request);

  if (request.action === "PROBE_YT_PLAYER") {
    try {
      const videos = Array.from(document.querySelectorAll("video"));
      const video = document.querySelector("video.html5-main-video") ||
        videos.find((item) => !item.paused && !item.ended) || videos[0] || null;
      const playing = !!video && !video.paused && !video.ended;
      const muted = !!video?.muted;
      const volume = Number(video?.volume ?? 0);
      const readyState = Number(video?.readyState ?? 0);
      const rawTitle = String(document.title || "");
      const channelNode = document.querySelector("#upload-info #channel-name") || document.querySelector("#channel-name");
      let videoId = "";
      try {
        const parsed = new URL(window.location.href);
        const partes = parsed.pathname.split("/").filter(Boolean);
        videoId = String(
          parsed.searchParams.get("v") ||
          (["shorts", "embed", "live"].includes(partes[0]) ? partes[1] : "") ||
          ""
        );
      } catch (_) {}
      const queue = _laylayYoutubeQueueSnapshot();
      sendResponse({
        ok: !!video,
        playing,
        audible: playing && !muted && volume > 0 && readyState >= 2,
        paused: !!video?.paused,
        muted,
        repeatEnabled: !!video?.loop,
        volumePercent: Number.isFinite(volume)
          ? Math.max(0, Math.min(100, Math.round(volume * 100))) : null,
        title: rawTitle.replace(/ - YouTube$/i, "").trim(),
        channel: _laylayYoutubeChannelText(channelNode),
        url: window.location.href,
        videoId,
        currentTime: Number.isFinite(video?.currentTime) ? Number(video.currentTime) : 0,
        duration: Number.isFinite(video?.duration) ? Number(video.duration) : 0,
        observedAt: Date.now(),
        positionReliable: !!video && Number.isFinite(video.currentTime),
        queueObserved: queue.observed,
        queue: queue.items,
      });
    } catch (_) {
      sendResponse({ ok: false, playing: false, audible: false });
    }
    return true;
  }
  
  // --- COMANDOS ADICIONAIS (Spinning Fish, Netflix, etc) ---
  if (request.action === "spinning_fish") {
    try {
        window.__laylay_fish_mode = true;
        const target = String(request.url || "https://spinning.fish/").trim();
        if (!location.href.includes("spinning.fish")) {
            try { window.focus(); } catch (_) {}
            try { window.location.href = target; } catch (_) {}
        }
        const tryFS = () => {
            const el = document.documentElement;
            const fn = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen;
            if (typeof fn === "function") {
                try { fn.call(el); } catch (_) {}
            }
        };
        if (document.readyState === "complete") {
            tryFS();
        } else {
            window.addEventListener("load", () => setTimeout(tryFS, 0), { once: true });
        }
        const onClickFS = () => {
            if (!window.__laylay_fish_mode) return;
            tryFS();
            document.removeEventListener("click", onClickFS, true);
        };
        document.addEventListener("click", onClickFS, true);
    } catch (_) {}
  }

  if (request.action === "close_current_tab") {
    try {
        const ae = document.activeElement;
        const tag = String(ae?.tagName || "").toLowerCase();
        const isInput = tag === "input" || tag === "textarea";
        const isEditable = isInput || !!ae?.isContentEditable;
        const val = isInput ? String(ae?.value || "") : String(ae?.textContent || "");
        
        if (isEditable && val.trim().length > 0) {
            try { sendMessage({ action: "close_tab_status", status: "blocked_form", url: window.location.href, title: document.title }); } catch (_) {}
            return;
        }
        try { sendMessage({ action: "close_tab_status", status: "closing", url: window.location.href, title: document.title }); } catch (_) {}
        try { chrome.runtime.sendMessage({ action: "close_me" }); } catch (_) {}
    } catch (_) {}
  }

  if (request.action === "netflix_control" && request.command) {
    const cmd = String(request.command || "").toLowerCase();
    if (cmd === "enter" || cmd === "play") {
        _dispatchKey("Enter", "Enter", 13);
    }
    if (cmd === "scan_and_enter") {
        try { _netflixInitDoneForUrl = ""; } catch (_) {}
        try { scannerNetlifx(); } catch (_) {}
    }
  }

  if (request.action === "start_netflix_navigation") {
    try { navegarAteLupa(request.movie); } catch (_) {}
  }

  if (request.action === "GET_YT_DATA") {
    try {
        const rawTitle = String(document.title || "");
        const title = rawTitle.replace(/ - YouTube$/i, "").trim();
        const ch = document.querySelector("#upload-info #channel-name") || document.querySelector("#channel-name");
        const canal = _laylayYoutubeChannelText(ch);
        const resultado = {
            type: "YOUTUBE_DATA", 
            requestId: request.requestId ?? null, 
            url: window.location.href, 
            title, 
            canal 
        };
        if (request.directResponse === true && typeof sendResponse === "function") {
          sendResponse(resultado);
        } else {
          sendMessage(resultado);
        }
    } catch (_) {
      if (request.directResponse === true && typeof sendResponse === "function") {
        sendResponse(null);
      }
    }
    return true;
  }

  if (request.action === "auto_click_first_result") {
    try {
        if (!_laylayAutoClickEnabledFromUrl()) return;
        clicarPrimeiroResultado();
    } catch (_) {}
  }
});

try {
  document.addEventListener("click", _captureClick, true);
  if (location.hostname.includes("youtube.com")) {
    document.addEventListener("click", (e) => {
      const t = e?.target;
      if (!t) return;
      const grid = t.closest && t.closest("ytd-rich-grid-media");
      const anchor = t.closest && t.closest("a#video-title");
      if (grid || anchor) {
        sendMessage({ type: "PLAYER_EVENT", event: "user_click_detected", url: location.href, title: document.title });
      }
    }, true);
    let _laylayPlaybackSerial = 0;
    let _laylayLastPlaybackKey = "";
    let _laylayLastPlayerStateAt = 0;
    let _laylayLastPlayerSignature = "";

    const _laylayVideoId = () => {
      try {
        return String(new URL(location.href).searchParams.get("v") || location.pathname || location.href);
      } catch (_) {
        return String(location.href || location.pathname || "youtube");
      }
    };

    const _emitLaylayVideoEnded = (v) => {
      if (!v) return;
      const videoId = _laylayVideoId();
      const playbackKey = `${videoId}:${_laylayPlaybackSerial}`;
      if (v.__laylayEndedPlaybackKey === playbackKey) return;

      const body = document.body;
      const player = document.querySelector(".html5-video-player");
      const isAdByClass =
        (body && (body.classList.contains("ad-showing") || body.classList.contains("ad-interrupting"))) ||
        (player && (player.classList.contains("ad-showing") || player.classList.contains("ad-interrupting")));
      const isAdByUrl = String(location.href).includes("ad_id") || String(location.href).includes("doubleclick");
      const isAd = !!isAdByClass || !!isAdByUrl;

      v.__laylayEndedPlaybackKey = playbackKey;
      sendMessage({
        type: "PLAYER_EVENT",
        event: "video_ended",
        eventId: `ended:${videoId}:${_laylayPlaybackSerial}:${Date.now()}`,
        url: location.href,
        title: document.title,
        isAd: !!isAd,
        duration: Number.isFinite(v.duration) ? Math.floor(v.duration) : 0,
      });
    };

    const _emitLaylayPlayerState = (v, force = false) => {
      if (!v) return;
      const now = Date.now();
      const state = v.ended ? "ended" : (v.paused ? "paused" : "playing");
      const position = Number.isFinite(v.currentTime) ? Number(v.currentTime) : 0;
      const duration = Number.isFinite(v.duration) ? Number(v.duration) : 0;
      const title = String(document.title || "").replace(/ - YouTube$/i, "").trim();
      const channelNode = document.querySelector("#upload-info #channel-name") || document.querySelector("#channel-name");
      const channel = _laylayYoutubeChannelText(channelNode);
      const volumePercent = Number.isFinite(v.volume)
        ? Math.max(0, Math.min(100, Math.round(v.volume * 100))) : null;
      const muted = !!v.muted;
      const repeatEnabled = !!v.loop;
      const signature = `${_laylayVideoId()}:${state}:${Math.floor(position)}:${Math.floor(duration)}:${volumePercent}:${muted}:${repeatEnabled}:${title}`;
      if (!force && signature === _laylayLastPlayerSignature && now - _laylayLastPlayerStateAt < 3000) return;
      if (!force && now - _laylayLastPlayerStateAt < 900) return;
      _laylayLastPlayerStateAt = now;
      _laylayLastPlayerSignature = signature;
      sendMessage({
        type: "PLAYER_EVENT",
        event: "player_state",
        url: location.href,
        videoId: _laylayVideoId(),
        title,
        channel,
        state,
        paused: !!v.paused,
        muted,
        volumePercent,
        repeatEnabled,
        currentTime: position,
        duration,
        observedAt: now,
      });
    };

    const _bindLaylayVideo = () => {
      const v = document.querySelector("video");
      if (!v) return;
      if (!v.__laylayBound) {
        v.__laylayBound = true;
        try {
          v.addEventListener("playing", () => {
            const key = `${_laylayVideoId()}:${String(v.currentSrc || v.src || "")}`;
            if (key !== _laylayLastPlaybackKey) {
              _laylayLastPlaybackKey = key;
              _laylayPlaybackSerial += 1;
              v.__laylayEndedPlaybackKey = "";
            }
            _emitLaylayPlayerState(v, true);
          });
          v.addEventListener("play", () => _emitLaylayPlayerState(v, true));
          v.addEventListener("pause", () => _emitLaylayPlayerState(v, true));
          v.addEventListener("loadedmetadata", () => _emitLaylayPlayerState(v, true));
          v.addEventListener("timeupdate", () => _emitLaylayPlayerState(v, false));
          v.addEventListener("ended", () => {
            _emitLaylayPlayerState(v, true);
            _emitLaylayVideoEnded(v);
          });
        } catch (_) {}
      }
      _emitLaylayPlayerState(v, false);
      // Recupera o caso raro em que o script entrou depois do evento nativo.
      if (v.ended && Number(v.currentTime || 0) > 0) _emitLaylayVideoEnded(v);
    };

    const vWatcher = new MutationObserver(_bindLaylayVideo);
    vWatcher.observe(document.documentElement || document, { childList: true, subtree: true });
    _bindLaylayVideo();
    setInterval(_bindLaylayVideo, 1000);
  }
  document.addEventListener("keydown", (e) => {
    const el = e?.target;
    if (_isImportantElement(el)) _markInteraction();
  }, true);
  document.addEventListener("input", (e) => {
    const el = e?.target;
    if (_isImportantElement(el)) _markInteraction();
  }, true);
  _hookHistory();
  _injectConsoleBridge();
  _listenConsoleBridge();
} catch (_) {}

try {
  setInterval(() => {
    if (location.href !== _lastUrl) {
      _lastUrl = location.href;
      _idleSent = false;
      return;
    }
    const idleMs = Date.now() - _lastInteractionTs;
    if (!_idleSent && idleMs >= 60000) {
      _idleSent = true;
      enviarContexto("idle", { idleMs, url: location.href, title: document.title });
    }
  }, 5000);
} catch (_) {}
