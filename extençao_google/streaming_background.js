// Compartilha a instalação da extensão; o transporte não acessa o canal da IA.
(() => {
  let socket = null;
  let retryAt = 0;
  const versions = new Map();

  async function inject(tabId) {
    try {
      await chrome.scripting.executeScript({
        target: {tabId, allFrames: true}, files: ["streaming_detector.js"]
      });
    } catch (_) {} // Páginas internas e origens sem permissão não são capturáveis.
  }

  async function injectActiveTabs() {
    const tabs = await chrome.tabs.query({active: true});
    await Promise.all(tabs.map(tab => inject(tab.id)));
  }

  function connect() {
    if (socket && socket.readyState <= WebSocket.OPEN) return;
    if (Date.now() < retryAt) return;
    retryAt = Date.now() + 2000;
    const current = new WebSocket("ws://127.0.0.1:19769");
    socket = current;
    current.onerror = () => {};
    current.onopen = () => {
      current.send(JSON.stringify({type: "streaming_hello", version: 1}));
      void injectActiveTabs().catch(() => {});
    };
  }

  chrome.runtime.onMessage.addListener((message, sender) => {
    if (message?.type !== "LAYLAY_STREAMING_LOCAL" || sender.frameId !== 0 || !sender.tab?.active) return;
    if (!Array.isArray(message.videos) || !message.viewport) return;
    const sequence = (versions.get(sender.tab.id) || 0) + 1;
    versions.set(sender.tab.id, sequence);
    connect();
    const current = socket;
    if (!current || current.readyState !== WebSocket.OPEN) return;
    Promise.all([chrome.tabs.getZoom(sender.tab.id), chrome.windows.get(sender.tab.windowId)]).then(([zoom, win]) => {
      if (versions.get(sender.tab.id) !== sequence || current !== socket || current.readyState !== WebSocket.OPEN) return;
      current.send(JSON.stringify({
        type: "videos", tabId: sender.tab.id, windowId: sender.tab.windowId,
        title: String(sender.tab.title || "").slice(0, 240),
        // outerWidth/outerHeight da página podem ser alterados por proteções
        // de privacidade. A API da extensão é dona dos limites da janela.
        viewport: {...message.viewport, outerWidth: win.width, outerHeight: win.height, zoom},
        videos: win.state === "minimized" ? [] : message.videos.slice(0, 20)
      }));
    }).catch(() => {});
  });

  chrome.tabs.onActivated.addListener(info => { void inject(info.tabId); });
  chrome.tabs.onUpdated.addListener((tabId, change, tab) => {
    if (tab.active && change.status === "complete") void inject(tabId);
  });
  chrome.tabs.onRemoved.addListener(tabId => versions.delete(tabId));
  // A conexão independe de haver vídeo ou de a IA estar ligada.
  // Heartbeat mantém o service worker ativo mesmo em páginas internas.
  setInterval(() => {
    connect();
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({type: "streaming_hello", version: 1}));
    }
  }, 2000);
  connect();
})();
