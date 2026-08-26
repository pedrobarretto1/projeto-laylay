
let websocket = null;
const WS_URL = "ws://localhost:8080";

let lastTargetTabId = null;
const pendingPlayerEvents = new Map();
let playerDiscoveryRunning = false;
let playerDiscoveryQueued = false;
let playerDiscoveryTimer = null;
const MEDIA_HISTORY_STORAGE_KEY = "laylayConfirmedMediaNavigationV1";
const MEDIA_HISTORY_TTL_MS = 30 * 60 * 1000;
const MEDIA_HISTORY_MAX_ITEMS = 12;

function youtubeVideoId(rawUrl) {
  try {
    const parsed = new URL(String(rawUrl || ""));
    if (!parsed.hostname.toLowerCase().endsWith("youtube.com")) return "";
    const parts = parsed.pathname.split("/").filter(Boolean);
    return String(
      parsed.searchParams.get("v") ||
      (["shorts", "embed", "live"].includes(parts[0]) ? parts[1] : "") ||
      ""
    ).trim();
  } catch (_) {
    return "";
  }
}

function sameYouTubeMedia(firstUrl, secondUrl) {
  const firstId = youtubeVideoId(firstUrl);
  const secondId = youtubeVideoId(secondUrl);
  if (firstId && secondId) return firstId === secondId;
  return String(firstUrl || "") === String(secondUrl || "");
}

async function loadConfirmedMediaHistory() {
  try {
    const stored = await chrome.storage.session.get(MEDIA_HISTORY_STORAGE_KEY);
    const history = stored?.[MEDIA_HISTORY_STORAGE_KEY];
    return history && typeof history === "object" ? history : {};
  } catch (_) {
    return {};
  }
}

async function saveConfirmedMediaHistory(history) {
  try {
    await chrome.storage.session.set({
      [MEDIA_HISTORY_STORAGE_KEY]: history && typeof history === "object"
        ? history : {},
    });
    return true;
  } catch (_) {
    return false;
  }
}

async function rememberConfirmedMediaNavigation(tabId, evidence = {}) {
  if (!Number.isInteger(tabId)) return false;
  const previousUrl = String(evidence.beforeUrl || "").trim();
  const currentUrl = String(
    evidence.afterUrl || evidence.currentUrl || ""
  ).trim();
  if (
    !youtubeVideoId(previousUrl)
    || !youtubeVideoId(currentUrl)
    || sameYouTubeMedia(previousUrl, currentUrl)
  ) return false;

  const history = await loadConfirmedMediaHistory();
  const key = String(tabId);
  const now = Date.now();
  const stack = Array.isArray(history[key]) ? history[key].filter((item) => (
    item && now - Number(item.createdAt || 0) <= MEDIA_HISTORY_TTL_MS
  )) : [];
  const latest = stack[stack.length - 1];
  if (!latest || !(
    sameYouTubeMedia(latest.previousUrl, previousUrl)
    && sameYouTubeMedia(latest.currentUrl, currentUrl)
  )) {
    stack.push({ previousUrl, currentUrl, createdAt: now });
  }
  history[key] = stack.slice(-MEDIA_HISTORY_MAX_ITEMS);
  return saveConfirmedMediaHistory(history);
}

async function matchingConfirmedMediaNavigation(tab) {
  if (!Number.isInteger(tab?.id)) return null;
  const history = await loadConfirmedMediaHistory();
  const key = String(tab.id);
  const now = Date.now();
  const stack = Array.isArray(history[key]) ? history[key].filter((item) => (
    item && now - Number(item.createdAt || 0) <= MEDIA_HISTORY_TTL_MS
  )) : [];
  history[key] = stack;
  await saveConfirmedMediaHistory(history);
  const receipt = stack[stack.length - 1] || null;
  return receipt && sameYouTubeMedia(tab.url, receipt.currentUrl)
    ? { receipt, history, key, stack }
    : null;
}

function updateTabUrl(tabId, url) {
  return new Promise((resolve) => {
    chrome.tabs.update(tabId, { url }, (tab) => {
      const error = chrome.runtime.lastError?.message || "";
      resolve(error ? { tab: null, error } : { tab: tab || null, error: "" });
    });
  });
}

async function observeTabMedia(tabId, expectedUrl, timeoutMs = 5000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const tab = await tabById(tabId);
    if (tab && sameYouTubeMedia(tab.url, expectedUrl)) return tab;
    await new Promise((resolve) => setTimeout(resolve, 120));
  }
  return null;
}

async function restoreConfirmedPreviousMedia(tab) {
  const matched = await matchingConfirmedMediaNavigation(tab);
  if (!matched) return null;
  const { receipt, history, key, stack } = matched;
  const update = await updateTabUrl(tab.id, receipt.previousUrl);
  if (update.error) {
    return {
      status: "history_restore_failed",
      message: update.error,
      evidence: { previousUrl: receipt.previousUrl, currentUrl: tab.url || "" },
    };
  }
  const observed = (
    update.tab && sameYouTubeMedia(update.tab.url, receipt.previousUrl)
  ) ? update.tab : await observeTabMedia(tab.id, receipt.previousUrl);
  if (!observed) {
    return {
      status: "history_restore_failed",
      message: "A URL musical anterior não foi observada após a restauração",
      evidence: { previousUrl: receipt.previousUrl, currentUrl: tab.url || "" },
    };
  }
  stack.pop();
  history[key] = stack;
  await saveConfirmedMediaHistory(history);
  return {
    status: "success",
    message: "",
    evidence: {
      previousUrl: receipt.previousUrl,
      currentUrl: observed.url || receipt.previousUrl,
      restoredBy: "confirmed_media_history",
      changed: true,
    },
  };
}

function safeJsonParse(text) {
  try { return JSON.parse(text); } catch (_) { return null; }
}

function sendWs(message) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) return false;
  try {
    websocket.send(JSON.stringify(message));
    return true;
  } catch (_) {
    return false;
  }
}

function queuePlayerEvent(message) {
  const eventId = String(message?.eventId || "").trim();
  if (!eventId) return;
  pendingPlayerEvents.set(eventId, message);
  while (pendingPlayerEvents.size > 24) {
    pendingPlayerEvents.delete(pendingPlayerEvents.keys().next().value);
  }
}

function flushPendingPlayerEvents() {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) return;
  for (const message of pendingPlayerEvents.values()) sendWs(message);
}

function sendCommandResult(cmd, ok, detail = {}, tab = null) {
  const status = String(detail?.status || (ok ? "success" : "error"));
  sendWs({
    type: "COMMAND_RESULT",
    requestId: cmd?.requestId ?? null,
    action: String(cmd?.action || ""),
    ok: Boolean(ok),
    status,
    message: String(detail?.message || ""),
    evidence: detail?.evidence || null,
    tab: tab ? { id: tab.id ?? null, url: tab.url || "", title: tab.title || "" } : null,
    ts: Date.now(),
  });
}

// P0_NAVEGADOR_JANELA_FOCADA_V4_2_20260815
// ``currentWindow`` no service worker não é sinônimo de janela visualmente em
// foco. Toda leitura operacional de "aba ativa" parte da última janela focada
// e consulta a aba com um windowId explícito.
function lastFocusedWindow() {
  return new Promise((resolve) => {
    chrome.windows.getLastFocused({}, (win) => {
      const error = chrome.runtime.lastError?.message || "";
      resolve(error ? null : (win || null));
    });
  });
}

function tabById(tabId) {
  return new Promise((resolve) => {
    if (!Number.isInteger(tabId)) {
      resolve(null);
      return;
    }
    chrome.tabs.get(tabId, (tab) => {
      const error = chrome.runtime.lastError?.message || "";
      resolve(error ? null : (tab || null));
    });
  });
}

function activeTabInWindow(windowId) {
  return new Promise((resolve) => {
    if (!Number.isInteger(windowId) || windowId === chrome.windows.WINDOW_ID_NONE) {
      resolve(null);
      return;
    }
    chrome.tabs.query({ active: true, windowId }, (tabs) => {
      resolve(tabs?.[0] || null);
    });
  });
}

async function activeTab() {
  const win = await lastFocusedWindow();
  if (!Number.isInteger(win?.id)) return null;
  return activeTabInWindow(win.id);
}

function sendToTab(tabId, message) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      const error = chrome.runtime.lastError?.message || "";
      resolve({ response: response || null, error });
    });
  });
}

function youtubeVideoId(rawUrl) {
  try {
    const parsed = new URL(String(rawUrl || ""));
    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    const parts = parsed.pathname.split("/").filter(Boolean);
    const candidate = host === "youtu.be"
      ? parts[0]
      : parsed.searchParams.get("v") ||
        (["shorts", "embed", "live"].includes(parts[0]) ? parts[1] : "");
    return /^[A-Za-z0-9_-]{11}$/.test(String(candidate || ""))
      ? String(candidate) : "";
  } catch (_) {
    return "";
  }
}

// Estas funções são executadas dentro da aba pelo service worker. Elas não
// dependem do content_script, portanto também enxergam abas que já estavam
// abertas quando a extensão foi instalada ou recarregada.
function inspectYouTubePlayerInPage() {
  try {
    const channelText = (node) => {
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
    };
    const videos = Array.from(document.querySelectorAll("video"));
    const video = document.querySelector("video.html5-main-video") ||
      videos.find((item) => !item.paused && !item.ended) || videos[0] || null;
    const playing = !!video && !video.paused && !video.ended;
    const muted = !!video?.muted;
    const volume = Number(video?.volume ?? 0);
    const readyState = Number(video?.readyState ?? 0);
    const rawTitle = String(document.title || "");
    const channelNode =
      document.querySelector("#upload-info #channel-name") ||
      document.querySelector("#channel-name") ||
      document.querySelector("ytmusic-player-bar .subtitle");
    let videoId = "";
    try {
      const parsed = new URL(location.href);
      const parts = parsed.pathname.split("/").filter(Boolean);
      videoId = String(
        parsed.searchParams.get("v") ||
        (["shorts", "embed", "live"].includes(parts[0]) ? parts[1] : "") ||
        ""
      ).slice(0, 80);
    } catch (_) {}
    const queueRoot = document.querySelector(
      "ytd-playlist-panel-renderer, ytmusic-player-queue, #playlist-items",
    );
    const queueRows = queueRoot ? Array.from(queueRoot.querySelectorAll(
      "ytd-playlist-panel-video-renderer, ytmusic-player-queue-item",
    )) : [];
    const queueSelected = queueRows.findIndex((row) => (
      row.hasAttribute("selected") || row.getAttribute("aria-selected") === "true" ||
      row.classList.contains("selected")
    ));
    const queueStart = queueSelected >= 0 ? queueSelected + 1 : 0;
    const queue = queueRows.slice(queueStart, queueStart + 8).map((row) => {
      const anchor = row.querySelector("a#wc-endpoint, a[href*='/watch'], a[href*='/shorts/']");
      const titleNode = row.querySelector("#video-title, .song-title, yt-formatted-string.title");
      const channelItem = row.querySelector("#byline, .byline, .subtitle, #channel-name");
      const durationNode = row.querySelector("#text, .badge-shape-wiz__text, .duration");
      const href = String(anchor?.href || anchor?.getAttribute("href") || "");
      let itemVideoId = "";
      try {
        const parsedItem = new URL(href, location.href);
        const itemParts = parsedItem.pathname.split("/").filter(Boolean);
        itemVideoId = String(
          parsedItem.searchParams.get("v") ||
          (["shorts", "embed", "live"].includes(itemParts[0]) ? itemParts[1] : "") || ""
        );
      } catch (_) {}
      const durationText = String(durationNode?.textContent || "").replace(/\s+/g, " ").trim();
      const durationParts = durationText.split(":").map((part) => Number(part));
      const durationSeconds = durationParts.every(Number.isFinite)
        ? durationParts.reduce((total, value) => total * 60 + value, 0) : 0;
      return {
        title: String(titleNode?.textContent || anchor?.textContent || "").replace(/\s+/g, " ").trim(),
        channel: channelText(channelItem),
        videoId: itemVideoId,
        durationSeconds,
      };
    }).filter((item) => item.title);
    return {
      ok: !!video,
      playing,
      audible: playing && !muted && volume > 0 && readyState >= 2,
      paused: !!video?.paused,
      muted,
      repeatEnabled: !!video?.loop,
      volumePercent: Number.isFinite(volume)
        ? Math.max(0, Math.min(100, Math.round(volume * 100))) : null,
      title: rawTitle.replace(/ - YouTube$/i, "").trim(),
      channel: channelText(channelNode),
      url: String(location.href || ""),
      videoId,
      currentTime: Number.isFinite(video?.currentTime) ? Number(video.currentTime) : 0,
      duration: Number.isFinite(video?.duration) ? Number(video.duration) : 0,
      observedAt: Date.now(),
      positionReliable: !!video && Number.isFinite(video.currentTime),
      queueObserved: !!queueRoot,
      queue,
    };
  } catch (_) {
    return { ok: false, playing: false, audible: false };
  }
}

function inspectYouTubeDataInPage() {
  try {
    const channelText = (node) => {
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
    };
    const rawTitle = String(document.title || "");
    const channelNode =
      document.querySelector("#upload-info #channel-name") ||
      document.querySelector("#channel-name") ||
      document.querySelector("ytmusic-player-bar .subtitle");
    return {
      url: String(location.href || ""),
      title: rawTitle.replace(/ - YouTube$/i, "").trim(),
      canal: channelText(channelNode),
    };
  } catch (_) {
    return null;
  }
}

function executeScriptResult(tabId, func) {
  return new Promise((resolve) => {
    chrome.scripting.executeScript(
      { target: { tabId }, world: "ISOLATED", func },
      (results) => {
        const error = chrome.runtime.lastError?.message || "";
        resolve({ response: results?.[0]?.result || null, error });
      },
    );
  });
}

async function probeYouTubeTab(tab) {
  if (tab?.id == null) return { tab, response: null, error: "missing_tab" };
  let result = await sendToTab(tab.id, { action: "PROBE_YT_PLAYER" });
  if (!result.response) {
    result = await executeScriptResult(tab.id, inspectYouTubePlayerInPage);
  }
  return { tab, response: result.response || null, error: result.error || "" };
}

async function readYouTubeTabData(tab, requestId = null) {
  if (tab?.id == null) return { response: null, error: "missing_tab" };
  let result = await sendToTab(tab.id, {
    action: "GET_YT_DATA", requestId, directResponse: true,
  });
  if (!result.response) {
    result = await executeScriptResult(tab.id, inspectYouTubeDataInPage);
  }
  return result;
}

async function findBestYouTubeCandidate(activeFallback = true) {
  const youtubeTabs = await new Promise((resolve) => {
    chrome.tabs.query({
      url: ["*://*.youtube.com/*", "*://youtube.com/*"],
    }, (tabs) => resolve(Array.isArray(tabs) ? tabs : []));
  });
  const probes = await Promise.all(youtubeTabs.map(probeYouTubeTab));
  const scored = probes.map((item) => {
    const tab = item.tab || {};
    const probe = item.response || {};
    let score = 0;
    if (probe.audible === true) score += 1000;
    else if (tab.audible === true) score += 800;
    if (probe.playing === true) score += 500;
    if (String(tab.url || "").includes("/watch")) score += 80;
    if (tab.active === true) score += 20;
    score += Math.min(10, Math.max(0, Number(tab.lastAccessed || 0) / 1e15));
    return { ...item, score };
  }).sort((a, b) => b.score - a.score);
  if (scored[0]) return scored[0];
  if (!activeFallback) return null;
  const active = await activeTab();
  return active ? { tab: active, response: null, score: 0 } : null;
}

async function discoverExistingYouTubePlayback() {
  if (playerDiscoveryRunning) {
    playerDiscoveryQueued = true;
    return false;
  }
  playerDiscoveryRunning = true;
  try {
    const escolhido = await findBestYouTubeCandidate(false);
    const tab = escolhido?.tab || null;
    const probe = escolhido?.response || {};
    const playerObserved = (
      probe.ok === true || probe.playing === true || probe.paused === true
    );
    if (!tab || !playerObserved) {
      return sendWs({
        type: "PLAYER_EVENT",
        event: "player_unavailable",
        source: "youtube_tabs_probe",
        authoritative: true,
        observedAt: Date.now(),
      });
    }
    const dataResult = await readYouTubeTabData(tab);
    const dados = dataResult.response || {};
    return sendWs({
      type: "PLAYER_EVENT",
      event: "player_state",
      source: (
        probe.audible === true || tab.audible === true ? "audible_youtube_tab"
          : probe.playing === true ? "playing_youtube_tab"
          : tab.active === true ? "active_youtube_tab"
          : "youtube_tab_fallback"
      ),
      authoritative: true,
      url: String(dados.url || probe.url || tab.url || ""),
      videoId: String(
        probe.videoId || dados.videoId ||
        youtubeVideoId(dados.url || probe.url || tab.url || "") || ""
      ),
      title: String(dados.title || probe.title || tab.title || "")
        .replace(/ - YouTube$/i, "").trim(),
      channel: String(dados.canal || probe.channel || ""),
      state: probe.playing === true ? "playing" : "paused",
      paused: probe.paused === true,
      muted: probe.muted === true || tab.mutedInfo?.muted === true,
      repeatEnabled: probe.repeatEnabled === true,
      volumePercent: Number.isFinite(Number(probe.volumePercent))
        ? Math.max(0, Math.min(100, Math.round(Number(probe.volumePercent))))
        : null,
      currentTime: Number(probe.currentTime || 0),
      duration: Number(probe.duration || 0),
      positionReliable: probe.positionReliable === true,
      queueObserved: probe.queueObserved === true,
      queue: Array.isArray(probe.queue) ? probe.queue.slice(0, 8) : [],
      tabId: tab.id ?? null,
      tabActive: tab.active === true,
      audibleConfirmed: probe.audible === true || tab.audible === true,
      playingConfirmed: probe.playing === true,
      observedAt: Number(probe.observedAt || Date.now()),
    });
  } finally {
    playerDiscoveryRunning = false;
    if (playerDiscoveryQueued) {
      playerDiscoveryQueued = false;
      setTimeout(() => void discoverExistingYouTubePlayback(), 120);
    }
  }
}

function schedulePlayerDiscovery(delayMs = 120) {
  if (playerDiscoveryTimer != null) clearTimeout(playerDiscoveryTimer);
  playerDiscoveryTimer = setTimeout(() => {
    playerDiscoveryTimer = null;
    void discoverExistingYouTubePlayback();
  }, Math.max(0, Number(delayMs) || 0));
}

function comparableUrl(rawUrl) {
  try {
    const parsed = new URL(String(rawUrl || ""));
    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    const path = (parsed.pathname || "/").replace(/\/+$/, "") || "/";
    return { host, path, query: parsed.searchParams.toString() };
  } catch (_) {
    return { host: "", path: "", query: "" };
  }
}

function equivalentTab(tabs, targetUrl) {
  const target = comparableUrl(targetUrl);
  if (!target.host) return null;
  const home = (target.path === "/" || target.path === "/.") && !target.query;
  return (tabs || []).find((tab) => {
    const current = comparableUrl(tab?.url || "");
    if (current.host !== target.host) return false;
    return home || (current.path === target.path && current.query === target.query);
  }) || null;
}

function focusTab(tab, callback = () => {}) {
  if (tab?.id == null) {
    callback(false, "Aba inválida");
    return;
  }
  chrome.tabs.update(tab.id, { active: true }, (updated) => {
    const tabError = chrome.runtime.lastError?.message || "";
    if (tabError) {
      callback(false, tabError);
      return;
    }
    chrome.windows.update(tab.windowId, { focused: true }, () => {
      const windowError = chrome.runtime.lastError?.message || "";
      callback(!windowError, windowError, updated || tab);
    });
  });
}

async function executeContentCommand(cmd, tab) {
  let attempt = await sendToTab(tab.id, cmd);
  if (attempt.error) {
    await new Promise((resolve) => {
      chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content_script.js"] }, () => resolve());
    });
    attempt = await new Promise((resolve) => setTimeout(async () => resolve(await sendToTab(tab.id, cmd)), 120));
  }
  if (attempt.error || !attempt.response) {
    return { status: "error", message: attempt.error || "A página não respondeu ao comando" };
  }
  return attempt.response;
}

function waitForTabComplete(tabId, timeoutMs = 9000) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (tab) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      chrome.tabs.onUpdated.removeListener(onUpdated);
      resolve(tab || null);
    };
    const onUpdated = (id, info, tab) => {
      if (id === tabId && info.status === "complete") finish(tab);
    };
    const timer = setTimeout(() => finish(null), timeoutMs);
    chrome.tabs.onUpdated.addListener(onUpdated);
    chrome.tabs.get(tabId, (tab) => {
      if (!chrome.runtime.lastError && tab?.status === "complete") finish(tab);
    });
  });
}

async function confirmYouTubeNavigation(cmd, tab, error = "", evidence = {}) {
  if (error || !tab?.id) {
    sendCommandResult(cmd, false, {
      status: "error",
      message: error || "A aba do YouTube não ficou disponível",
      evidence,
    }, tab);
    return;
  }
  if (cmd?.action !== "youtube_play") {
    sendCommandResult(cmd, true, {
      status: "playlist_tab_updated",
      evidence,
    }, tab);
    return;
  }

  const readyTab = await waitForTabComplete(tab.id);
  if (!readyTab) {
    sendCommandResult(cmd, false, {
      status: "navigation_timeout",
      message: "O vídeo não terminou de carregar a tempo",
      evidence,
    }, tab);
    return;
  }
  const response = await executeContentCommand({
    action: "youtube_control",
    command: "play",
    verify_playback: true,
  }, readyTab);
  const playing = response?.evidence?.playing === true;
  const tabMuted = readyTab?.mutedInfo?.muted === true;
  const audible = response?.status === "success"
    && response?.evidence?.audible === true
    && !tabMuted;
  sendCommandResult(cmd, audible, {
    status: audible ? "playing_confirmed" : (response?.status || "autoplay_blocked"),
    message: audible ? "" : (
      tabMuted
        ? "O vídeo iniciou, mas a aba do navegador está silenciada"
        : (response?.message || "O player não iniciou a reprodução")
    ),
    evidence: {
      ...evidence,
      ...(response?.evidence || {}),
      playing,
      audible,
      tabMuted,
    },
  }, readyTab);
}

async function handleCommand(cmd) {
  if (!cmd || typeof cmd !== "object") return;

  // --- COMANDOS DE INTERFACE (CLICK, TYPE, SCROLL, PRESS, ETC) ---
  const uiActions = ["click", "type", "press", "scroll", "search_in_page", "close_current_tab"];
  if (uiActions.includes(cmd.action)) {
    const tab = await activeTab();
    if (!tab?.id) {
      sendCommandResult(cmd, false, { status: "error", message: "Nenhuma aba ativa encontrada" });
      return;
    }
    const expectedUrl = String(cmd.expectedUrl || cmd.expected_url || "").trim();
    const expectedTabId = Number(cmd.expectedTabId ?? cmd.expected_tab_id);
    if (Number.isFinite(expectedTabId) && tab.id !== expectedTabId) {
      sendCommandResult(cmd, false, { status: "stale_context", message: "A aba ativa mudou antes da execução" }, tab);
      return;
    }
    if (expectedUrl && String(tab.url || "") !== expectedUrl) {
      sendCommandResult(cmd, false, { status: "stale_context", message: "A aba mudou antes da execução" }, tab);
      return;
    }
    if (cmd.action === "type") {
      const sensitiveMarkers = ["login", "signin", "sign-in", "password", "senha", "checkout", "pagamento", "payment", "bank", "banco", "internetbanking", "wallet"];
      if (sensitiveMarkers.some((marker) => String(tab.url || "").toLowerCase().includes(marker))) {
        sendCommandResult(cmd, false, { status: "sensitive_page", message: "Digitação automática bloqueada em página sensível" }, tab);
        return;
      }
    }
    if (cmd.action === "close_current_tab") {
      chrome.tabs.remove(tab.id, () => {
        const error = chrome.runtime.lastError?.message || "";
        sendCommandResult(cmd, !error, { status: error ? "error" : "success", message: error }, tab);
      });
      return;
    }
    const response = await executeContentCommand(cmd, tab);
    const ok = response?.status === "success" || response?.status === "partial";
    sendCommandResult(cmd, ok, response || {}, tab);
    console.log(`${ok ? "✅" : "⚠️"} Resultado ${cmd.action} na aba ${tab.id}:`, response);
    return;
  }

  // --- FECHAR ABA ESPECÍFICA ---
  if (cmd.action === "close_tab") {
    const target = String(cmd.title || (cmd.payload ? cmd.payload.title : "")).toLowerCase().trim();
    if (!target) return;

    chrome.tabs.query({}, (tabs) => {
      const tabToClose = tabs.find(t => 
        (t.title && t.title.toLowerCase().includes(target)) || 
        (t.url && t.url.toLowerCase().includes(target))
      );

      if (tabToClose && tabToClose.id) {
        chrome.tabs.remove(tabToClose.id);
        console.log(`❌ Aba fechada [${target}]:`, tabToClose.id);
      } else {
        console.warn(`⚠️ Nenhuma aba encontrada para fechar com o termo: ${target}`);
      }
    });
    return;
  }

if (cmd.action === "youtube_search") {
  const query = String(cmd.query || "").trim();
  if (!query) return;
  const background = cmd.background === true;

  // URL formatada para busca de vídeos apenas
  const url = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}&sp=EgIQAQ%253D%253D`;

  chrome.tabs.query({ url: "*://*.youtube.com/*" }, (tabs) => {
    // Prioridade máxima: aba que já está tocando um vídeo
    let targetTab = tabs.find(t => t.url && t.url.includes("/watch?v=")) ||
                    tabs.find(t => t.url && t.url.includes("/watch")) ||
                    tabs[0];

    if (targetTab && targetTab.id) {
      // REUSO INTELIGENTE: atualiza a aba existente
      chrome.tabs.update(targetTab.id, { url: url, active: !background }, (tab) => {
        lastTargetTabId = tab?.id ?? targetTab.id;
        console.log("🚀 Laylay reutilizou aba YouTube:", targetTab.id);
      });

      // FOCO TOTAL: traz a janela para frente (mesmo se estiver minimizada ou em outra janela)
      if (!background && targetTab.windowId != null) {
        chrome.windows.update(targetTab.windowId, { focused: true });
      }
    } else {
      // Só cria nova aba se realmente não tiver nenhuma do YouTube
      chrome.tabs.create({ url, active: !background }, (tab) => {
        lastTargetTabId = tab?.id ?? null;
        console.log("🚀 Laylay criou nova aba YouTube (nenhuma encontrada).");
      });
    }
  });
  return;
}

  // --- CONTROLES DE MÍDIA (YOUTUBE / YOUTUBE MUSIC) ---
  if (cmd.action === "youtube_control") {
    const comando = String(cmd.command || (cmd.payload && cmd.payload.command) || "").trim();
    const tabs = await new Promise((resolve) => {
      chrome.tabs.query({ url: "*://*.youtube.com/*" }, (lista) => resolve(lista || []));
    });
    const requestedTabId = Number(cmd.target_tab_id ?? cmd.targetTabId);
    let targetTab = Number.isInteger(requestedTabId)
      ? tabs.find((tab) => tab.id === requestedTabId)
      : null;
    if (!Number.isInteger(requestedTabId)) {
      // A aba visível pode ser Wikipédia, código ou qualquer outra página.
      // Controle de mídia pertence à aba que realmente tem um player
      // reproduzindo/pausado, não à primeira aba do YouTube retornada.
      const melhor = await findBestYouTubeCandidate(false);
      targetTab = melhor?.tab || null;
    }
    if (!targetTab?.id) {
      sendCommandResult(cmd, false, {
        status: Number.isInteger(requestedTabId) ? "source_tab_missing" : "not_found",
        message: Number.isInteger(requestedTabId)
          ? "A aba de mídia observada não está mais disponível"
          : "Nenhuma aba do YouTube encontrada",
        evidence: { requestedTabId: Number.isInteger(requestedTabId) ? requestedTabId : null },
      });
      return;
    }
    if (comando === "prev") {
      const restored = await restoreConfirmedPreviousMedia(targetTab);
      if (restored?.status === "success") {
        sendCommandResult(cmd, true, restored, targetTab);
        console.log(
          `📺 Controle do YouTube [prev] restaurou histórico confirmado na aba ${targetTab.id}:`,
          restored,
        );
        return;
      }
    }
    const response = await executeContentCommand({
      ...cmd,
      action: "youtube_control",
      command: comando,
      payload: { ...(cmd.payload || {}), command: comando },
    }, targetTab);
    const ok = response?.status === "success" || response?.status === "partial";
    if (comando === "next" && ok) {
      await rememberConfirmedMediaNavigation(targetTab.id, response?.evidence || {});
    }
    sendCommandResult(cmd, ok, response || {}, targetTab);
    console.log(`${ok ? "📺" : "⚠️"} Controle do YouTube [${comando}] na aba ${targetTab.id}:`, response);
    return;
  }

  if (cmd.action === "netflix_search") {
    const query = String(cmd.query || "").trim();
    if (!query) return;
    const url = `https://www.netflix.com/.`;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const active = tabs && tabs[0] ? tabs[0] : null;
      if (active?.id != null && typeof active.url === "string" && active.url.includes("netflix.com")) {
        chrome.tabs.update(active.id, { url, active: true }, (tab) => {
          lastTargetTabId = tab?.id ?? active.id;
        });
      } else {
        chrome.tabs.create({ url, active: true }, (tab) => {
          lastTargetTabId = tab?.id ?? null;
        });
      }
    });
    return;
  }

  if (cmd.action === "start_netflix_navigation") {
    const movie = String(cmd.movie || cmd.query || "").trim();
    if (!movie) return;
    const payload = { action: "start_netflix_navigation", movie };
    chrome.tabs.query({ url: ["*://*.netflix.com/*", "*://netflix.com/*"] }, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      if (list.length === 0) return;
      const sorted = list.slice().sort((a, b) => {
        const ab = typeof a.url === "string" && a.url.includes("netflix.com") ? 1 : 0;
        const bb = typeof b.url === "string" && b.url.includes("netflix.com") ? 1 : 0;
        return bb - ab;
      });
      const target = sorted[0];
      if (target?.id != null) {
        chrome.tabs.sendMessage(target.id, payload);
      }
    });
    return;
  }

if (cmd.action === "open_url" || cmd.action === "youtube_play") {
  let url = String(cmd.url || (cmd.payload ? cmd.payload.url : "")).trim();
  if (!url) {
    console.warn("⚠️ open_url/youtube_play chamado sem URL");
    return;
  }

  const isYouTube = url.includes("youtube.com") || url.includes("youtu.be");
  const autoClick = cmd.auto_click === true || String(url).includes("laylay_auto=true");
  const background = cmd.background === true;

  if (isYouTube) {
    console.log("🚀 [YouTube Strong Reuse] Usando aba única para:", url);

    const requestedTabId = Number(cmd.target_tab_id ?? cmd.targetTabId);
    if (Number.isInteger(requestedTabId)) {
      chrome.tabs.get(requestedTabId, (sourceTab) => {
        const error = chrome.runtime.lastError?.message || "";
        const sourceIsYouTube = sourceTab?.id != null && /(?:youtube\.com|youtu\.be)/i.test(String(sourceTab.url || ""));
        if (error || !sourceIsYouTube) {
          sendCommandResult(cmd, false, { status: "source_tab_missing", message: error || "A aba da playlist não existe mais" });
          return;
        }
        chrome.tabs.update(sourceTab.id, { url, active: !background }, (updatedTab) => {
          const updateError = chrome.runtime.lastError?.message || "";
          if (!updateError) {
            lastTargetTabId = sourceTab.id;
            if (!background) chrome.windows.update(sourceTab.windowId, { focused: true });
          }
          void confirmYouTubeNavigation(
            cmd, updatedTab || sourceTab, updateError,
            { reused: true, playlistTab: true },
          );
        });
      });
      return;
    }

    // PRIORIDADE 1: Última aba que usamos (lastTargetTabId) - mais confiável
    if (lastTargetTabId != null) {
      chrome.tabs.get(lastTargetTabId, (tab) => {
        if (chrome.runtime.lastError || !tab || !tab.id) {
          lastTargetTabId = null; // aba foi fechada
          // Se falhou, tenta a busca normal (Prioridade 2)
          realizarBuscaYouTube(url, background, cmd);
        } else if (tab.url && tab.url.includes("youtube.com")) {
          // Atualiza a mesma aba (é isso que queremos!)
          chrome.tabs.update(lastTargetTabId, { url: url, active: !background }, (updatedTab) => {
            const updateError = chrome.runtime.lastError?.message || "";
            if (!updateError) {
              lastTargetTabId = updatedTab ? updatedTab.id : lastTargetTabId;
              if (!background && tab.windowId) chrome.windows.update(tab.windowId, { focused: true });
              console.log(`♻️ REUTILIZOU aba YouTube ID=${lastTargetTabId}`);
            }
            void confirmYouTubeNavigation(
              cmd, updatedTab || tab, updateError,
              { reused: true, playlistTab: true },
            );
          });
        } else {
          // Se a aba existe mas não é YouTube, tenta a busca normal
          realizarBuscaYouTube(url, background, cmd);
        }
      });
      return;
    }

    // PRIORIDADE 2: Busca normal (caso lastTargetTabId tenha morrido)
    realizarBuscaYouTube(url, background, cmd);
    return;
  }

  // Sites normais: foca somente uma aba equivalente; nunca substitui a aba atual.
  console.log(`🌐 open_url seguro: ${url}`);
  chrome.tabs.query({}, (tabs) => {
    const existing = equivalentTab(tabs, url);
    if (existing?.id != null) {
      if (background) {
        sendCommandResult(cmd, true, {
          status: "already_open_background",
          evidence: { reused: true, requestedUrl: url, background: true },
        }, existing);
        return;
      }
      focusTab(existing, (ok, error, focused) => {
        sendCommandResult(cmd, ok, {
          status: ok ? "already_open_focused" : "error",
          message: error || "",
          evidence: { reused: true, requestedUrl: url },
        }, focused || existing);
      });
      return;
    }
    chrome.tabs.create({ url: url, active: !background }, (tab) => {
      const error = chrome.runtime.lastError?.message || "";
      if (error || !tab) {
        sendCommandResult(cmd, false, { status: "error", message: error || "Não consegui criar a aba" });
        return;
      }
      if (!background && tab.windowId != null) chrome.windows.update(tab.windowId, { focused: true });
      sendCommandResult(cmd, true, {
        status: "new_tab_created",
        evidence: { reused: false, requestedUrl: url },
      }, tab);
        if (autoClick) {
          const tid = tab.id;
          const onUpdated = (id, info) => {
            if (id !== tid) return;
            if (info.status === "complete") {
              chrome.tabs.onUpdated.removeListener(onUpdated);
              chrome.tabs.sendMessage(tid, { action: "auto_click_first_result" });
            }
          };
          chrome.tabs.onUpdated.addListener(onUpdated);
        }
    });
  });
  return;
}

// Função auxiliar para evitar repetição de código
function realizarBuscaYouTube(url, background = false, cmd = null) {
  chrome.tabs.query({ url: "*://*.youtube.com/*" }, (tabs) => {
    let targetTab = tabs.find(t => t.url && (t.url.includes("/watch?v=") || t.url.includes("/watch"))) ||
                    tabs.find(t => t.url && t.url.includes("youtube.com")) ||
                    tabs[0];

    if (targetTab && targetTab.id) {
      chrome.tabs.update(targetTab.id, { url: url, active: !background }, (updatedTab) => {
        const updateError = chrome.runtime.lastError?.message || "";
        if (!updateError) {
          lastTargetTabId = updatedTab ? updatedTab.id : targetTab.id;
          if (!background && targetTab.windowId) chrome.windows.update(targetTab.windowId, { focused: true });
          console.log(`♻️ REUTILIZOU aba YouTube ID=${lastTargetTabId}`);
        }
        if (cmd) void confirmYouTubeNavigation(
          cmd, updatedTab || targetTab, updateError,
          { reused: true, playlistTab: true },
        );
      });
    } else {
      // Só cria nova se realmente não tiver nenhuma aba YouTube
      chrome.tabs.create({ url: url, active: !background }, (newTab) => {
        const createError = chrome.runtime.lastError?.message || "";
        if (!createError) {
          lastTargetTabId = newTab ? newTab.id : null;
          console.log("🆕 Criou nova aba YouTube (nenhuma encontrada)");
        }
        if (cmd) void confirmYouTubeNavigation(
          cmd, newTab, createError,
          { reused: false, playlistTab: true },
        );
      });
    }
  });
}

  // Bloco de volume removido para centralização no Python (OS level)

  if (cmd.action === "netflix_control" && cmd.command) {
    const payload = { action: "netflix_control", command: String(cmd.command) };
    chrome.tabs.query({ url: ["*://*.netflix.com/*", "*://netflix.com/*"] }, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      if (list.length === 0) return;
      const sorted = list.slice().sort((a, b) => {
        const ab = typeof a.url === "string" && a.url.includes("/browse") ? 1 : 0;
        const bb = typeof b.url === "string" && b.url.includes("/browse") ? 1 : 0;
        return bb - ab;
      });
      const target = sorted[0];
      if (target?.id != null) {
        chrome.tabs.sendMessage(target.id, payload);
      }
    });
    return;
  }

  if (cmd.action === "spinning_fish") {
    const url = String(cmd.url || "https://spinning.fish/").trim();
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const active = tabs && tabs[0] ? tabs[0] : null;
      const nav = () => {
        const targetId = active?.id ?? null;
        if (targetId != null) {
          chrome.tabs.update(targetId, { url, active: true }, (tab) => {
            const tid = tab?.id ?? targetId;
            const onUpdated = (id, info) => {
              if (id !== tid) return;
              if (info.status === "complete") {
                chrome.tabs.onUpdated.removeListener(onUpdated);
                chrome.tabs.sendMessage(tid, { action: "spinning_fish", url, force_fullscreen: true });
              }
            };
            chrome.tabs.onUpdated.addListener(onUpdated);
          });
        } else {
          chrome.tabs.create({ url, active: true }, (tab) => {
            const tid = tab?.id ?? null;
            if (tid == null) return;
            const onUpdated = (id, info) => {
              if (id !== tid) return;
              if (info.status === "complete") {
                chrome.tabs.onUpdated.removeListener(onUpdated);
                chrome.tabs.sendMessage(tid, { action: "spinning_fish", url, force_fullscreen: true });
              }
            };
            chrome.tabs.onUpdated.addListener(onUpdated);
          });
        }
      };
      nav();
    });
    return;
  }

  if (cmd.action === "reload_url" && cmd.url) {
    const url = String(cmd.url || "").trim();
    if (!url) return;
    chrome.tabs.query({}, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      const found = list.find((t) => typeof t.url === "string" && t.url === url);
      if (found?.id != null) {
        chrome.tabs.reload(found.id);
        return;
      }
      chrome.tabs.query({ active: true, currentWindow: true }, (ts) => {
        const active = ts && ts[0] ? ts[0] : null;
        if (active?.id != null) chrome.tabs.reload(active.id);
      });
    });
    return;
  }

  if (cmd.action === "get_active_tab_url") {
    const requestId = cmd.requestId ?? null;
    // A confirmação usa a mesma definição de aba ativa do monitor proativo:
    // aba ativa da última janela Chrome focada, nunca ``currentWindow``.
    const t = await activeTab();
    const url = t?.url || "";
    const title = t?.title || "";
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      // P0_NAVEGADOR_ACTIVE_TAB_PAYLOAD_V4_20260815
      websocket.send(JSON.stringify({
        type: "ACTIVE_TAB_URL",
        requestId,
        url,
        title,
        tabId: Number.isInteger(t?.id) ? t.id : null,
        windowId: Number.isInteger(t?.windowId) ? t.windowId : null,
        active: t?.active === true,
      }));
    }
    return;
  }

  if (cmd.action === "get_youtube_data") {
    const requestId = cmd.requestId ?? null;
    const escolhido = await findBestYouTubeCandidate(true);
    const t = escolhido?.tab || null;
    const probe = escolhido?.response || {};
    let dados = null;
    if (t?.id != null) {
      const result = await readYouTubeTabData(t, requestId);
      dados = result.response || null;
    }
    sendWs({
      type: "YOUTUBE_DATA",
      requestId,
      url: String(dados?.url || probe.url || t?.url || ""),
      title: String(dados?.title || probe.title || t?.title || "").replace(/ - YouTube$/i, "").trim(),
      canal: String(dados?.canal || probe.channel || ""),
      tabId: t?.id ?? null,
      source: (
        probe.audible === true || t?.audible === true ? "audible_youtube_tab"
          : probe.playing === true ? "playing_youtube_tab"
          : "youtube_tab_fallback"
      ),
      playingConfirmed: probe.playing === true,
      audibleConfirmed: probe.audible === true || t?.audible === true,
    });
    return;
  }

  if (cmd.action === "get_page_content") {
    const requestId = cmd.requestId ?? null;
    const reply = (success, data = {}, error = "") => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "PAGE_CONTENT", requestId, success, data, error }));
      }
    };
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs && tabs[0] ? tabs[0] : null;
      if (tab?.id == null) {
        reply(false, {}, "Nenhuma aba ativa encontrada");
        return;
      }
      const url = String(tab.url || "");
      if (/^(chrome|edge|about|opera|chrome-extension):/i.test(url)) {
        reply(false, { url, title: tab.title || "" }, "Esta página é protegida pelo navegador");
        return;
      }
      const solicitar = (permitirInjecao) => {
        chrome.tabs.sendMessage(tab.id, { action: "GET_PAGE_CONTENT", requestId }, (response) => {
          if (chrome.runtime.lastError || !response) {
            if (permitirInjecao) {
              chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content_script.js"] }, () => {
                if (chrome.runtime.lastError) {
                  reply(false, { url, title: tab.title || "" }, chrome.runtime.lastError.message);
                  return;
                }
                setTimeout(() => solicitar(false), 100);
              });
              return;
            }
            reply(false, { url, title: tab.title || "" }, chrome.runtime.lastError?.message || "A página não respondeu");
            return;
          }
          reply(response.success !== false, response.data || {}, response.error || "");
        });
      };
      solicitar(true);
    });
    return;
  }

  if (cmd.action === "update_tab" && cmd.url && cmd.tabId != null) {
    const url = String(cmd.url || "").trim();
    const tabId = Number(cmd.tabId);
    const autoClick = cmd.auto_click === true;
    if (!url || !Number.isInteger(tabId)) return;
    chrome.tabs.update(tabId, { url, active: true }, (tab) => {
      lastTargetTabId = tab?.id ?? tabId;
      if (autoClick) {
        const tid = tab?.id ?? tabId;
        const onUpdated = (id, info) => {
          if (id !== tid) return;
          if (info.status === "complete") {
            chrome.tabs.onUpdated.removeListener(onUpdated);
            chrome.tabs.sendMessage(tid, { action: "auto_click_first_result" });
          }
        };
        chrome.tabs.onUpdated.addListener(onUpdated);
      }
    });
    return;
  }

  if (cmd.action === "focus_tab" && cmd.tabId != null) {
    const tabId = Number(cmd.tabId);
    if (!Number.isInteger(tabId)) {
      sendCommandResult(cmd, false, { status: "error", message: "Identificador de aba inválido" });
      return;
    }
    chrome.tabs.get(tabId, (tab) => {
      const error = chrome.runtime.lastError?.message || "";
      if (error || !tab) {
        sendCommandResult(cmd, false, { status: "error", message: error || "Aba não encontrada" });
        return;
      }
      focusTab(tab, (ok, focusError, focused) => {
        sendCommandResult(cmd, ok, {
          status: ok ? "already_open_focused" : "error",
          message: focusError || "",
          evidence: { reused: true },
        }, focused || tab);
      });
    });
    return;
  }

  if (cmd.action === "get_tabs_list") {
    const requestId = cmd.requestId ?? null;
    chrome.tabs.query({}, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      const out = list
        .filter((t) => t && t.id != null)
        .map((t) => ({
          id: t.id,
          url: t.url || "",
          title: t.title || "",
          active: t.active === true,
          audible: t.audible === true,
          pinned: t.pinned === true,
          discarded: t.discarded === true,
          lastAccessed: Number.isFinite(t.lastAccessed) ? t.lastAccessed : null,
          windowId: Number.isInteger(t.windowId) ? t.windowId : null,
        }));
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "TABS_LIST", requestId, tabs: out }));
      }
    });
    return;
  }

  if (cmd.action === "click_first_result") {
    const requestedQuery = String(cmd.query || "").trim().toLowerCase();
    chrome.tabs.query({}, async (tabs) => {
      const normalize = (value) => String(value || "")
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .toLowerCase().replace(/\s+/g, " ").trim();
      const searches = (Array.isArray(tabs) ? tabs : []).filter((tab) => {
        try {
          const parsed = new URL(String(tab?.url || ""));
          return parsed.hostname.includes("google.") && parsed.pathname.startsWith("/search");
        } catch (_) {
          return false;
        }
      });
      const matching = searches.filter((tab) => {
        if (!requestedQuery) return true;
        try {
          const query = new URL(String(tab.url || "")).searchParams.get("q") || "";
          return normalize(query) === normalize(requestedQuery);
        } catch (_) {
          return false;
        }
      });
      const ordered = (matching.length ? matching : searches).slice().sort((a, b) => {
        const activeDiff = Number(b?.active === true) - Number(a?.active === true);
        if (activeDiff) return activeDiff;
        return Number(b?.lastAccessed || 0) - Number(a?.lastAccessed || 0);
      });
      const target = ordered[0] || null;
      if (!target?.id) {
        sendCommandResult(cmd, false, {
          status: "search_context_missing",
          message: "Nenhuma página de resultados observada",
        });
        return;
      }
      try {
        const injections = await chrome.scripting.executeScript({
          target: { tabId: target.id },
          func: () => {
            const adMarker = /(Patrocinado|Anúncio|Anuncio)/i;
            const headings = Array.from(document.querySelectorAll("div#search a h3"));
            for (const heading of headings) {
              const link = heading.closest ? heading.closest("a[href]") : null;
              const href = String(link?.href || "").trim();
              if (!href || !/^https?:\/\//i.test(href)) continue;
              if (/googleadservices|\/aclk\?|adurl=|\/search\?/i.test(href)) continue;
              let node = link;
              let sponsored = false;
              for (let depth = 0; depth < 7 && node; depth += 1) {
                if (adMarker.test(String(node.textContent || ""))) {
                  sponsored = true;
                  break;
                }
                node = node.parentElement;
              }
              if (sponsored) continue;
              return {
                href,
                title: String(heading.textContent || "").replace(/\s+/g, " ").trim(),
              };
            }
            return null;
          },
        });
        const selected = injections?.[0]?.result || null;
        if (!selected?.href) {
          sendCommandResult(cmd, false, {
            status: "result_not_found",
            message: "Nenhum resultado orgânico observável foi encontrado",
          }, target);
          return;
        }
        chrome.tabs.update(target.id, { url: selected.href, active: true }, (updated) => {
          const error = chrome.runtime.lastError?.message || "";
          if (!error && target.windowId != null) {
            try { chrome.windows.update(target.windowId, { focused: true }); } catch (_) {}
          }
          sendCommandResult(cmd, !error, {
            status: error ? "error" : "result_opened",
            message: error,
            evidence: {
              selectedUrl: selected.href,
              selectedTitle: selected.title || "",
              sourceTabId: target.id,
            },
          }, updated || target);
        });
      } catch (error) {
        sendCommandResult(cmd, false, {
          status: "error",
          message: String(error?.message || error || "Falha ao ler resultados"),
        }, target);
      }
    });
    return;
  }

  if (cmd.action === "check_tabs") {
    const requestId = cmd.requestId ?? null;
    const targetDomain = String(cmd.target_domain || cmd.targetDomain || "").trim().toLowerCase();
    if (!targetDomain) {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "CHECK_TABS_RESULT", requestId, tabId: null }));
      }
      return;
    }
    const patterns = [`*://*.${targetDomain}/*`, `*://${targetDomain}/*`];
    chrome.tabs.query({ url: patterns }, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      const normHostOk = (u) => {
        try {
          const url = new URL(String(u || ""));
          const h = String(url.hostname || "").toLowerCase();
          if (targetDomain === "google.com" && h.startsWith("gemini.")) return false;
          return h === targetDomain || h.endsWith(`.${targetDomain}`);
        } catch (_) {
          return false;
        }
      };
      const isPlayingOrBusy = (t) => {
        const u = String(t?.url || "");
        if (!u) return false;
        if (t?.audible === true) return true;
        const low = u.toLowerCase();
        if (low.includes("youtube.com/watch") || low.includes("/watch?v=")) return true;
        if (low.includes("netflix.com/watch")) return true;
        return false;
      };
      const isIdleHome = (t) => {
        const u = String(t?.url || "");
        if (!u) return false;
        try {
          const url = new URL(u);
          const h = String(url.hostname || "").toLowerCase();
          const p = String(url.pathname || "");
          if (h.includes("youtube.com")) {
            return p === "/" || p === "/results";
          }
          if (h.includes("netflix.com")) {
            return p === "/" || p === "/." || p.startsWith("/browse");
          }
          if (h.includes("google.com")) {
            return p === "/" || p.startsWith("/search");
          }
          return p === "/" || p === "/.";
        } catch (_) {
          return false;
        }
      };

      const candidates = list.filter((t) => t?.id != null && normHostOk(t.url));
      const idle = candidates.filter((t) => isIdleHome(t) && !isPlayingOrBusy(t));
      const chosen = idle.length > 0 ? idle[0] : null;
      const tabId = chosen?.id ?? null;
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "CHECK_TABS_RESULT", requestId, tabId }));
      }
    });
    return;
  }

  if (cmd.action === "close_current_tab") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      const tid = t?.id ?? null;
      if (tid == null) return;
      try {
        chrome.windows.update(t.windowId, { focused: true });
      } catch (_) {}
      chrome.tabs.sendMessage(tid, { action: "close_current_tab" }, () => {
        if (chrome.runtime.lastError) {
          try { chrome.tabs.remove(tid); } catch (_) {}
        }
      });
    });
    return;
  }

  if (cmd.action === "close_specific_tab") {
    const targetName = String(cmd.target || (cmd.payload && cmd.payload.target) || "").trim();
    if (!targetName) {
      sendCommandResult(cmd, false, { status: "invalid_target", message: "Alvo vazio" });
      return;
    }

    chrome.tabs.query({}, function(tabs) {
      const normalize = (value) => String(value || "")
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
      const wanted = normalize(targetName);
      const compact = wanted.replace(/\s+/g, "");
      const candidates = (Array.isArray(tabs) ? tabs : []).map((tab) => {
        const title = normalize(tab?.title);
        const url = normalize(tab?.url);
        let host = "";
        try { host = normalize(new URL(String(tab?.url || "")).hostname); } catch (_) {}
        const compactHost = host.replace(/\s+/g, "");
        let score = 0;
        if (title === wanted) score = 120;
        else if (host === wanted || host.endsWith(` ${wanted}`)) score = 115;
        else if (compact && compactHost.includes(compact)) score = 105;
        else if (wanted && title.includes(wanted)) score = 95;
        else if (wanted && url.includes(wanted)) score = 85;
        return { tab, score };
      }).filter((item) => item.score > 0 && item.tab?.id != null)
        .sort((a, b) => b.score - a.score || Number(b.tab.active) - Number(a.tab.active));
      const chosen = candidates[0]?.tab || null;
      if (!chosen?.id) {
        console.log("Nenhuma aba encontrada com o nome: " + targetName);
        sendCommandResult(cmd, false, {
          status: "not_found",
          message: "Nenhuma aba observada corresponde ao alvo",
        });
        return;
      }
      chrome.tabs.remove(chosen.id, () => {
        const error = chrome.runtime.lastError?.message || "";
        sendCommandResult(cmd, !error, {
          status: error ? "error" : "success",
          message: error,
          evidence: { closedTabId: chosen.id, target: targetName },
        }, chosen);
      });
    });
    return;
  }

  if (cmd.action === "close_tabs" && Array.isArray(cmd.ids)) {
    const ids = cmd.ids.filter((x) => Number.isInteger(x)).map((x) => Number(x));
    if (ids.length > 0) {
      chrome.tabs.remove(ids, () => {
        const error = chrome.runtime.lastError?.message || "";
        sendCommandResult(cmd, !error, {
          status: error ? "error" : "success",
          message: error,
          evidence: { closedTabIds: ids },
        });
      });
    } else {
      sendCommandResult(cmd, false, {
        status: "invalid_target", message: "Nenhum identificador de aba válido",
      });
    }
    return;
  }

  if (cmd.action === "click" || cmd.action === "type" || cmd.action === "press") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs[0] && tabs[0].id) {
            const tabId = tabs[0].id;
            chrome.tabs.sendMessage(tabId, cmd, (response) => {
                if (chrome.runtime.lastError) {
                    console.warn("⚠️ Content script não detectado. Tentando injetar manualmente...");
                    chrome.scripting.executeScript({
                        target: { tabId: tabId },
                        files: ["content_script.js"]
                    }, () => {
                        setTimeout(() => {
                            chrome.tabs.sendMessage(tabId, cmd);
                        }, 100);
                    });
                } else {
                    console.log(`✅ Laylay executou ${cmd.action} com sucesso na aba ${tabId}`);
                }
            });
        }
    });
    return;
  }
}

function connectWebSocket() {
  if (websocket && (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING)) return;

  console.log(`[Laylay] Conectando ao servidor Python em ${WS_URL}...`);
  websocket = new WebSocket(WS_URL);

  websocket.onopen = () => {
    console.log("[Laylay] WebSocket CONECTADO!");
    sendWs({
      type: "EXTENSION_HELLO",
      protocolVersion: 2,
      capabilities: [
        "page_snapshot", "command_result", "element_id",
        "stale_context_guard", "canonical_player_sync_v2",
        "queue_item_select_v1",
      ],
      message: "Extension connected",
    });
    sendActiveTabInfo(true);
    flushPendingPlayerEvents();
    void discoverExistingYouTubePlayback();
  };

  websocket.onmessage = async (event) => {
    const cmd = safeJsonParse(event.data);
    if (!cmd) return;
    if (cmd.type === "PLAYER_EVENT_ACK") {
      pendingPlayerEvents.delete(String(cmd.eventId || ""));
      return;
    }
    if (cmd.type !== "ping") console.log("[Laylay] Comando recebido:", cmd);
    await handleCommand(cmd);
  };

  websocket.onclose = (event) => {
    console.warn(`[Laylay] WebSocket desconectado (codigo ${event.code}). Reconectando em 3s...`);
    websocket = null;
    setTimeout(connectWebSocket, 3000);
  };

  websocket.onerror = (error) => {
    console.error("[Laylay] Erro no WebSocket:", error);
    // Fecha limpo - onclose vai agendar a reconexao
    try { websocket.close(); } catch (_) {}
  };
}

// Liga assim que a extensao carrega
connectWebSocket();

// Heartbeat a cada 5s: mantém conexão viva e reconecta se cair
setInterval(() => {
  if (!websocket || websocket.readyState === WebSocket.CLOSED || websocket.readyState === WebSocket.CLOSING) {
    console.log("[Laylay] Heartbeat: reconectando...");
    connectWebSocket();
  } else if (websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({ type: "ping", message: "heartbeat" }));
    flushPendingPlayerEvents();
    // O estado do player é efêmero. Renovamos a observação junto do
    // heartbeat para manter faixa, progresso e controles sincronizados mesmo
    // quando a aba já existia antes da extensão ou perdeu seus listeners.
    schedulePlayerDiscovery(0);
  }
}, 5000);

chrome.runtime.onMessage.addListener((request, sender) => {
  if (request && typeof request === "object" && request.action === "close_me") {
    const tabId = sender?.tab?.id ?? null;
    if (tabId != null) {
      try { chrome.tabs.remove(tabId); } catch (_) {}
    }
    return;
  }
  const source = sender?.tab ? { tabId: sender.tab.id ?? null, windowId: sender.tab.windowId ?? null } : {};
  const outgoing = request && typeof request === "object" && (request.type === "USER_CONTEXT" || request.type === "PLAYER_EVENT" || request.action === "title_update" || request.action === "user_context")
    ? { type: "USER_CONTEXT", ...request, ...source }
    : { ...request, ...source };
  if (request?.type === "PLAYER_EVENT" && request?.event === "video_ended") {
    queuePlayerEvent(outgoing);
  }
  if (request?.type === "PLAYER_EVENT" && request?.event === "player_state") {
    // Várias abas do YouTube possuem seu próprio content script. Encaminhar
    // todas diretamente criava uma corrida em que uma aba pausada antiga
    // podia sobrescrever a faixa audível. O background elege uma única aba.
    schedulePlayerDiscovery(80);
    return;
  }
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    if (outgoing && typeof outgoing === "object") {
      websocket.send(JSON.stringify(outgoing));
    } else {
      websocket.send(JSON.stringify(request));
    }
  } else {
    console.warn("[Laylay] WS fora do ar. Reconectando...");
    connectWebSocket();
  }
});

// --- MONITORAMENTO PROATIVO DA ABA ATIVA ---
function publishActiveTabInfo(t, includeSnapshot = false) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) return false;
  if (!t || !Number.isInteger(t.id)) return false;

  const url = String(t.url || "");
  if (!url || url.startsWith("chrome://") || url.startsWith("edge://")) return false;

  sendWs({
    action: "active_tab_changed",
    tabId: t.id,
    windowId: Number.isInteger(t.windowId) ? t.windowId : null,
    active: t.active === true,
    url,
    title: t.title || "Sem título",
  });

  if (includeSnapshot) {
    chrome.tabs.sendMessage(t.id, { action: "GET_PAGE_SNAPSHOT" }, (response) => {
      if (!chrome.runtime.lastError && response?.success) {
        sendWs({ type: "PAGE_SNAPSHOT", payload: response.data || {} });
      }
    });
  }
  return true;
}

async function sendActiveTabInfo(includeSnapshot = false) {
  const t = await activeTab();
  return publishActiveTabInfo(t, includeSnapshot);
}

async function sendActiveTabInfoForWindow(windowId, includeSnapshot = false) {
  const t = await activeTabInWindow(windowId);
  return publishActiveTabInfo(t, includeSnapshot);
}

async function sendActiveTabInfoById(tabId, windowId, includeSnapshot = false) {
  if (!Number.isInteger(tabId) || !Number.isInteger(windowId)) return false;

  // ``tabs.onActivated`` também pode ser disparado por uma ativação
  // programática numa janela que ainda não ganhou foco. Só aceitamos o evento
  // como estado global se ele pertence à última janela focada. Quando a janela
  // ganhar foco, ``windows.onFocusChanged`` fará a sincronização definitiva.
  const win = await lastFocusedWindow();
  if (!Number.isInteger(win?.id) || win.id !== windowId) return false;

  const t = await tabById(tabId);
  if (!t || t.windowId !== windowId || t.active !== true) return false;
  return publishActiveTabInfo(t, includeSnapshot);
}

chrome.tabs.onActivated.addListener((activeInfo) => {
  void sendActiveTabInfoById(activeInfo.tabId, activeInfo.windowId);
  schedulePlayerDiscovery(80);
});

chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) return;
  void sendActiveTabInfoForWindow(windowId);
  schedulePlayerDiscovery(80);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.title)) {
    void sendActiveTabInfoById(tabId, tab.windowId);
  }
  if (
    String(tab?.url || "").includes("youtube.com") &&
    (changeInfo.url || changeInfo.title || changeInfo.audible !== undefined || changeInfo.status === "complete")
  ) {
    schedulePlayerDiscovery(180);
  }
}); 

chrome.tabs.onRemoved.addListener(() => {
  schedulePlayerDiscovery(80);
});

