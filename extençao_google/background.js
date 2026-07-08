
let websocket = null;
const WS_URL = "ws://localhost:8080";

let lastTargetTabId = null;

function safeJsonParse(text) {
  try { return JSON.parse(text); } catch (_) { return null; }
}

async function handleCommand(cmd) {
  if (!cmd || typeof cmd !== "object") return;

  // --- COMANDOS DE INTERFACE (CLICK, TYPE, SCROLL, PRESS, ETC) ---
  const uiActions = ["click", "type", "press", "scroll", "execute_js", "close_current_tab"];
  if (uiActions.includes(cmd.action)) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (activeTab && activeTab.id) {
        if (cmd.action === "close_current_tab") {
          chrome.tabs.remove(activeTab.id);
          console.log("❌ Aba atual fechada:", activeTab.id);
        } else {
          chrome.tabs.sendMessage(activeTab.id, cmd);
          console.log(`🖥️ Comando de UI enviado para aba ${activeTab.id}:`, cmd.action);
        }
      }
    });
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

  // URL formatada para busca de vídeos apenas
  const url = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}&sp=EgIQAQ%253D%253D`;

  chrome.tabs.query({ url: "*://*.youtube.com/*" }, (tabs) => {
    // Prioridade máxima: aba que já está tocando um vídeo
    let targetTab = tabs.find(t => t.url && t.url.includes("/watch?v=")) ||
                    tabs.find(t => t.url && t.url.includes("/watch")) ||
                    tabs[0];

    if (targetTab && targetTab.id) {
      // REUSO INTELIGENTE: atualiza a aba existente
      chrome.tabs.update(targetTab.id, { url: url, active: true }, (tab) => {
        lastTargetTabId = tab?.id ?? targetTab.id;
        console.log("🚀 Laylay reutilizou aba YouTube:", targetTab.id);
      });

      // FOCO TOTAL: traz a janela para frente (mesmo se estiver minimizada ou em outra janela)
      if (targetTab.windowId != null) {
        chrome.windows.update(targetTab.windowId, { focused: true });
      }
    } else {
      // Só cria nova aba se realmente não tiver nenhuma do YouTube
      chrome.tabs.create({ url, active: true }, (tab) => {
        lastTargetTabId = tab?.id ?? null;
        console.log("🚀 Laylay criou nova aba YouTube (nenhuma encontrada).");
      });
    }
  });
  return;
}

  // --- CONTROLES DE MÍDIA (YOUTUBE / YOUTUBE MUSIC) ---
  if (cmd.action === "youtube_control") {
    // Pega o comando (seja vindo direto em cmd.command ou dentro de cmd.payload)
    const comando = cmd.command || (cmd.payload && cmd.payload.command);
    
    // Procura por qualquer aba do YouTube aberta
    chrome.tabs.query({ url: "*://*.youtube.com/*" }, (tabs) => {
      // Prioriza a aba que tem um vídeo tocando ("/watch")
      let targetTab = tabs.find(t => t.url && t.url.includes("/watch")) || tabs[0];
      
      if (targetTab && targetTab.id) {
        // Injeta o script direto na aba para forçar a ação no player
        chrome.scripting.executeScript({
          target: { tabId: targetTab.id },
          func: (acao) => {
            const video = document.querySelector('video');
            
            if (acao === "pause" && video) {
                video.pause();
            } else if (acao === "play" && video) {
                video.play();
            } else if (acao === "next") {
                const nextBtn = document.querySelector('.ytp-next-button');
                if (nextBtn) nextBtn.click();
            } else if (acao === "prev") {
                const prevBtn = document.querySelector('.ytp-prev-button');
                if (prevBtn) {
                    prevBtn.click();
                    setTimeout(() => {
                        try {
                            const videoNow = document.querySelector('video');
                            if (videoNow && videoNow.currentTime < 3) prevBtn.click();
                        } catch (_) {}
                    }, 180);
                }
            } else if (acao === "replay") {
                if (video) video.currentTime = 0;
                else {
                    const prevBtn = document.querySelector('.ytp-prev-button');
                    if (prevBtn) prevBtn.click();
                }
            }
          },
          args: [comando]
        });
        console.log(`📺 Sucesso! Comando de mídia [${comando}] aplicado na aba: ${targetTab.id}`);
      } else {
        console.warn("⚠️ Nenhuma aba do YouTube encontrada para controlar.");
      }
    });
    
    return; // Para a execução aqui, já resolvemos o comando
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

  if (isYouTube) {
    console.log("🚀 [YouTube Strong Reuse] Usando aba única para:", url);

    // PRIORIDADE 1: Última aba que usamos (lastTargetTabId) - mais confiável
    if (lastTargetTabId != null) {
      chrome.tabs.get(lastTargetTabId, (tab) => {
        if (chrome.runtime.lastError || !tab || !tab.id) {
          lastTargetTabId = null; // aba foi fechada
          // Se falhou, tenta a busca normal (Prioridade 2)
          realizarBuscaYouTube(url);
        } else if (tab.url && tab.url.includes("youtube.com")) {
          // Atualiza a mesma aba (é isso que queremos!)
          chrome.tabs.update(lastTargetTabId, { url: url, active: true }, (updatedTab) => {
            lastTargetTabId = updatedTab ? updatedTab.id : lastTargetTabId;
            if (tab.windowId) chrome.windows.update(tab.windowId, { focused: true });
            console.log(`♻️ REUTILIZOU aba YouTube ID=${lastTargetTabId}`);
          });
        } else {
          // Se a aba existe mas não é YouTube, tenta a busca normal
          realizarBuscaYouTube(url);
        }
      });
      return;
    }

    // PRIORIDADE 2: Busca normal (caso lastTargetTabId tenha morrido)
    realizarBuscaYouTube(url);
    return;
  }

  // Sites normais (não-YouTube) - comportamento antigo
  console.log(`🔄 open_url normal: ${url}`);
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const activeTab = tabs && tabs[0] ? tabs[0] : null;
    if (activeTab && activeTab.id) {
      chrome.tabs.update(activeTab.id, { url: url, active: true }, (tab) => {
        if (autoClick) {
          const tid = tab?.id ?? activeTab.id;
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
    } else {
      chrome.tabs.create({ url: url, active: true }, (tab) => {
        if (autoClick && tab?.id != null) {
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
    }
  });
  return;
}

// Função auxiliar para evitar repetição de código
function realizarBuscaYouTube(url) {
  chrome.tabs.query({ url: "*://*.youtube.com/*" }, (tabs) => {
    let targetTab = tabs.find(t => t.url && (t.url.includes("/watch?v=") || t.url.includes("/watch"))) ||
                    tabs.find(t => t.url && t.url.includes("youtube.com")) ||
                    tabs[0];

    if (targetTab && targetTab.id) {
      chrome.tabs.update(targetTab.id, { url: url, active: true }, (updatedTab) => {
        lastTargetTabId = updatedTab ? updatedTab.id : targetTab.id;
        if (targetTab.windowId) chrome.windows.update(targetTab.windowId, { focused: true });
        console.log(`♻️ REUTILIZOU aba YouTube ID=${lastTargetTabId}`);
      });
    } else {
      // Só cria nova se realmente não tiver nenhuma aba YouTube
      chrome.tabs.create({ url: url, active: true }, (newTab) => {
        lastTargetTabId = newTab ? newTab.id : null;
        console.log("🆕 Criou nova aba YouTube (nenhuma encontrada)");
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
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      const url = t?.url || "";
      const title = t?.title || "";
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "ACTIVE_TAB_URL", requestId, url, title }));
      }
    });
    return;
  }

  if (cmd.action === "get_youtube_data") {
    const requestId = cmd.requestId ?? null;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      const url = t?.url || "";
      const title = t?.title || "";
      if (t?.id != null) {
        chrome.tabs.sendMessage(t.id, { action: "GET_YT_DATA", requestId }, () => {
          if (chrome.runtime.lastError) {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify({ type: "YOUTUBE_DATA", requestId, url, title, canal: "" }));
            }
          }
        });
      } else {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({ type: "YOUTUBE_DATA", requestId, url, title, canal: "" }));
        }
      }
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

  if (cmd.action === "get_tabs_list") {
    const requestId = cmd.requestId ?? null;
    chrome.tabs.query({}, (tabs) => {
      const list = Array.isArray(tabs) ? tabs : [];
      const out = list
        .filter((t) => t && t.id != null)
        .map((t) => ({ id: t.id, url: t.url || "", title: t.title || "" }));
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: "TABS_LIST", requestId, tabs: out }));
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
    const targetName = String(cmd.target || (cmd.payload && cmd.payload.target) || "").toLowerCase();
    if (!targetName) return;

    chrome.tabs.query({}, function(tabs) {
      let abaFechada = false;
      for (let tab of tabs) {
        let titulo = tab.title ? tab.title.toLowerCase() : "";
        let url = tab.url ? tab.url.toLowerCase() : "";
        if (titulo.includes(targetName) || url.includes(targetName)) {
          chrome.tabs.remove(tab.id);
          console.log("💀 Aba eliminada: " + tab.title);
          abaFechada = true;
        }
      }
      if (!abaFechada) {
        console.log("Nenhuma aba encontrada com o nome: " + targetName);
      }
    });
    return;
  }

  if (cmd.action === "close_tabs" && Array.isArray(cmd.ids)) {
    const ids = cmd.ids.filter((x) => Number.isInteger(x)).map((x) => Number(x));
    if (ids.length > 0) {
      chrome.tabs.remove(ids);
    }
    return;
  }

  if (cmd.action === "click" || cmd.action === "type" || cmd.action === "press" || cmd.action === "execute_js") {
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
    websocket.send(JSON.stringify({ type: "ping", message: "Extension connected" }));
  };

  websocket.onmessage = async (event) => {
    const cmd = safeJsonParse(event.data);
    if (!cmd) return;
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
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    if (request && typeof request === "object" && (request.type === "USER_CONTEXT" || request.type === "PLAYER_EVENT" || request.action === "title_update" || request.action === "user_context")) {
      websocket.send(JSON.stringify({ type: "USER_CONTEXT", ...request }));
    } else {
      websocket.send(JSON.stringify(request));
    }
  } else {
    console.warn("[Laylay] WS fora do ar. Reconectando...");
    connectWebSocket();
  }
});

// --- MONITORAMENTO PROATIVO DA ABA ATIVA ---
function sendActiveTabInfo() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      if (t && t.url && !t.url.startsWith("chrome://") && !t.url.startsWith("edge://")) {
        websocket.send(JSON.stringify({ 
          action: "active_tab_changed", 
          url: t.url, 
          title: t.title || "Sem título" 
        }));
      }
    });
  }
}

chrome.tabs.onActivated.addListener(() => {
  sendActiveTabInfo();
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.title)) {
    sendActiveTabInfo();
  }
}); 

