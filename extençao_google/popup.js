const statusNode = document.getElementById("status");
const syncButton = document.getElementById("sincronizar");
const stopButton = document.getElementById("parar");

function mostrarStatus(texto, tipo = "idle") {
  statusNode.textContent = String(texto || "");
  statusNode.dataset.kind = tipo;
}

function videoIdYouTube(rawUrl) {
  try {
    const url = new URL(String(rawUrl || ""));
    if (!url.hostname.toLowerCase().endsWith("youtube.com")) return "";
    const partes = url.pathname.split("/").filter(Boolean);
    return String(
      url.searchParams.get("v") ||
      (["shorts", "live", "embed"].includes(partes[0]) ? partes[1] : "") ||
      ""
    ).trim();
  } catch (_) {
    return "";
  }
}

async function garantirDocumentoOffscreen() {
  if (typeof chrome.runtime.getContexts === "function") {
    const contextos = await chrome.runtime.getContexts({
      contextTypes: ["OFFSCREEN_DOCUMENT"],
      documentUrls: [chrome.runtime.getURL("offscreen.html")],
    });
    if (contextos.length) return;
  }
  try {
    await chrome.offscreen.createDocument({
      url: "offscreen.html",
      reasons: ["USER_MEDIA"],
      justification: "Analisar somente a batida da aba musical autorizada pelo usuário",
    });
  } catch (erro) {
    if (!String(erro?.message || erro).includes("single offscreen")) throw erro;
  }
}

function enviarAba(tabId, mensagem) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, mensagem, (resposta) => {
      void chrome.runtime.lastError;
      resolve(resposta || null);
    });
  });
}

async function abaAtiva() {
  const abas = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  return abas[0] || null;
}

async function sincronizar() {
  syncButton.disabled = true;
  mostrarStatus("Confirmando o player desta aba…", "pending");
  try {
    const tab = await abaAtiva();
    const videoId = videoIdYouTube(tab?.url);
    if (!tab || !Number.isInteger(tab.id) || !videoId) {
      throw new Error("Abra a faixa do YouTube que está tocando e tente novamente.");
    }
    const canonica = await chrome.runtime.sendMessage({
      type: "GET_CANONICAL_MUSIC_TAB",
    });
    if (canonica?.tabId !== tab.id) {
      throw new Error(
        canonica?.title
          ? `A Laylay está ouvindo outra aba: ${canonica.title}`
          : "Esta não é a aba musical confirmada pela Laylay.",
      );
    }
    const probe = await enviarAba(tab.id, { action: "PROBE_YT_PLAYER" });
    if (!(probe?.playing === true || tab.audible === true)) {
      throw new Error("Dê play nessa aba do YouTube antes de sincronizar.");
    }
    await garantirDocumentoOffscreen();
    const streamId = await chrome.tabCapture.getMediaStreamId({
      targetTabId: tab.id,
    });
    if (!streamId) throw new Error("O Chrome não liberou o áudio desta aba.");
    const resposta = await chrome.runtime.sendMessage({
      target: "offscreen",
      type: "START_MUSIC_METER",
      streamId,
      tabId: tab.id,
      videoId,
    });
    if (resposta?.ok !== true) {
      throw new Error(resposta?.message || "Não consegui iniciar o analisador.");
    }
    await chrome.storage.session.set({
      laylayMusicMeter: { active: true, tabId: tab.id, videoId, title: tab.title || "" },
    });
    mostrarStatus("Batida sincronizada somente com esta aba.", "ok");
  } catch (erro) {
    mostrarStatus(String(erro?.message || erro || "Falha ao sincronizar."), "error");
  } finally {
    syncButton.disabled = false;
  }
}

async function parar() {
  await garantirDocumentoOffscreen();
  await chrome.runtime.sendMessage({ target: "offscreen", type: "STOP_MUSIC_METER" });
  await chrome.storage.session.set({ laylayMusicMeter: { active: false } });
  mostrarStatus("Sincronização parada. O indicador voltou ao modo livre.", "idle");
}

syncButton.addEventListener("click", sincronizar);
stopButton.addEventListener("click", parar);

void garantirDocumentoOffscreen().catch(() => {});
void chrome.storage.session.get("laylayMusicMeter").then((dados) => {
  const medidor = dados?.laylayMusicMeter;
  if (medidor?.active === true) {
    mostrarStatus("Sincronização ativa em uma aba do YouTube.", "ok");
  }
});
