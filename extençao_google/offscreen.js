let media = null;
let output = null;
let source = null;
let analyser = null;
let intervalId = null;
let frequencyData = null;
let timeData = null;
let owner = { tabId: null, videoId: "" };
let peaks = [0.06, 0.06, 0.06];

function limitar(valor, minimo = 0, maximo = 1) {
  return Math.max(minimo, Math.min(maximo, Number(valor) || 0));
}

function mediaFaixa(dados, inicioHz, fimHz) {
  if (!analyser || !dados?.length) return 0;
  const hzPorBin = output.sampleRate / analyser.fftSize;
  const inicio = Math.max(0, Math.floor(inicioHz / hzPorBin));
  const fim = Math.min(dados.length - 1, Math.ceil(fimHz / hzPorBin));
  let soma = 0;
  let quantidade = 0;
  for (let indice = inicio; indice <= fim; indice += 1) {
    soma += dados[indice] / 255;
    quantidade += 1;
  }
  return quantidade ? soma / quantidade : 0;
}

function publicarAmostra() {
  if (!analyser || !frequencyData || !timeData) return;
  analyser.getByteFrequencyData(frequencyData);
  analyser.getByteTimeDomainData(timeData);
  let quadrados = 0;
  for (const amostra of timeData) {
    const normalizada = (amostra - 128) / 128;
    quadrados += normalizada * normalizada;
  }
  const rms = Math.sqrt(quadrados / Math.max(1, timeData.length));
  const bandas = [
    mediaFaixa(frequencyData, 45, 180),
    mediaFaixa(frequencyData, 180, 2000),
    mediaFaixa(frequencyData, 2000, 8000),
  ];
  const silencio = rms < 0.006;
  const levels = bandas.map((valor, indice) => {
    peaks[indice] = Math.max(0.04, valor, peaks[indice] * 0.992);
    if (silencio) return 0;
    return Number(limitar((valor / peaks[indice] - 0.06) / 0.94).toFixed(4));
  });
  chrome.runtime.sendMessage({
    type: "MUSIC_METER_SAMPLE",
    tabId: owner.tabId,
    videoId: owner.videoId,
    levels,
    energy: Number(limitar(rms * 4.5).toFixed(4)),
    observedAt: Date.now(),
  }).catch(() => {});
}

async function pararMedidor(notificar = true) {
  if (intervalId != null) clearInterval(intervalId);
  intervalId = null;
  for (const track of media?.getTracks?.() || []) track.stop();
  media = null;
  try { source?.disconnect(); } catch (_) {}
  source = null;
  analyser = null;
  frequencyData = null;
  timeData = null;
  if (output) await output.close().catch(() => {});
  output = null;
  owner = { tabId: null, videoId: "" };
  peaks = [0.06, 0.06, 0.06];
  if (notificar) {
    chrome.runtime.sendMessage({ type: "MUSIC_METER_STOPPED" }).catch(() => {});
  }
}

async function iniciarMedidor(request) {
  await pararMedidor(false);
  owner = {
    tabId: Number.isInteger(request.tabId) ? request.tabId : null,
    videoId: String(request.videoId || ""),
  };
  if (owner.tabId == null || !request.streamId) {
    throw new Error("A aba musical autorizada não foi informada.");
  }
  media = await navigator.mediaDevices.getUserMedia({
    audio: {
      mandatory: {
        chromeMediaSource: "tab",
        chromeMediaSourceId: request.streamId,
      },
    },
    video: false,
  });
  output = new AudioContext();
  source = output.createMediaStreamSource(media);
  analyser = output.createAnalyser();
  analyser.fftSize = 512;
  analyser.smoothingTimeConstant = 0.46;
  source.connect(analyser);
  // tabCapture silencia a reprodução original. Reconectar o stream preserva
  // a música para o usuário sem misturar qualquer outra fonte do sistema.
  source.connect(output.destination);
  frequencyData = new Uint8Array(analyser.frequencyBinCount);
  timeData = new Uint8Array(analyser.fftSize);
  for (const track of media.getTracks()) {
    track.addEventListener("ended", () => void pararMedidor(true), { once: true });
  }
  intervalId = setInterval(publicarAmostra, 50);
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request?.target !== "offscreen") return false;
  if (request.type === "START_MUSIC_METER") {
    iniciarMedidor(request).then(
      () => sendResponse({ ok: true }),
      (erro) => sendResponse({ ok: false, message: String(erro?.message || erro) }),
    );
    return true;
  }
  if (request.type === "UPDATE_MUSIC_METER_OWNER") {
    if (request.tabId === owner.tabId) owner.videoId = String(request.videoId || "");
    sendResponse({ ok: true });
    return false;
  }
  if (request.type === "STOP_MUSIC_METER") {
    pararMedidor(true).then(() => sendResponse({ ok: true }));
    return true;
  }
  return false;
});
