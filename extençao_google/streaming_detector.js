(() => {
  // Reinjeção em páginas já abertas não duplica timers nem identidades.
  if (globalThis.__laylayStreamingDetectorV1) return;
  globalThis.__laylayStreamingDetectorV1 = true;
  const channel = "LAYLAY_STREAMING_RECT_V1";
  const frameKey = [...crypto.getRandomValues(new Uint32Array(4))].join("-");
  const ids = new WeakMap();
  const children = new Map();
  let sequence = 0;
  let discoveredAt = 0, cachedVideos = [];
  const number = value => Number.isFinite(value) ? value : 0;
  function clip(rect, box) {
    const x = Math.max(rect.x, box.x), y = Math.max(rect.y, box.y);
    return {...rect, x, y, width: Math.max(0, Math.min(rect.x + rect.width, box.x + box.width) - x),
      height: Math.max(0, Math.min(rect.y + rect.height, box.y + box.height) - y)};
  }
  function findVideos(root = document) {
    const result = [...root.querySelectorAll("video")];
    for (const element of root.querySelectorAll("*")) {
      if (element.shadowRoot) result.push(...findVideos(element.shadowRoot));
    }
    return result;
  }
  function localVideos() {
    if (document.visibilityState !== "visible") return [];
    const root = document.documentElement;
    const rootStyle = getComputedStyle(root);
    const bodyStyle = document.body ? getComputedStyle(document.body) : null;
    const bodyOverflowOnViewport = root.tagName === "HTML"
      && rootStyle.overflowX === "visible" && rootStyle.overflowY === "visible"
      && rootStyle.contain === "none" && bodyStyle?.contain === "none";
    if (performance.now() - discoveredAt > 1000 || !discoveredAt) {
      cachedVideos = findVideos(); discoveredAt = performance.now();
    }
    return cachedVideos.filter(video => video.isConnected).flatMap(video => {
      const box = video.getBoundingClientRect(), style = getComputedStyle(video);
      if (!video.videoWidth || !video.videoHeight || style.visibility !== "visible" || Number(style.opacity) === 0) return [];
      const sx = box.width / (video.offsetWidth || box.width), sy = box.height / (video.offsetHeight || box.height);
      let x = box.x + (parseFloat(style.borderLeftWidth) + parseFloat(style.paddingLeft)) * sx;
      let y = box.y + (parseFloat(style.borderTopWidth) + parseFloat(style.paddingTop)) * sy;
      let width = (video.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)) * sx;
      let height = (video.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom)) * sy;
      // Uma caixa CSS pode conter barras. Usa o tamanho do conteúdo de vídeo.
      if (["contain", "scale-down"].includes(style.objectFit)) {
        const ratio = Math.min(style.objectFit === "scale-down" ? 1 : Infinity, width / video.videoWidth, height / video.videoHeight);
        const w = video.videoWidth * ratio, h = video.videoHeight * ratio;
        const position = style.objectPosition.split(" ");
        const px = position[0]?.endsWith("%") ? parseFloat(position[0]) / 100 : .5;
        const py = position[1]?.endsWith("%") ? parseFloat(position[1]) / 100 : .5;
        x += (width - w) * px; y += (height - h) * py; width = w; height = h;
      }
      let visible = clip({x, y, width, height}, {x: 0, y: 0, width: innerWidth, height: innerHeight});
      for (let ancestor = video; ancestor; ancestor = ancestor.parentElement) {
        const css = getComputedStyle(ancestor);
        if (css.transform.startsWith("matrix(")) {
          const matrix = css.transform.slice(7, -1).split(",").map(Number);
          if (Math.abs(matrix[1]) > .001 || Math.abs(matrix[2]) > .001) return [];
        } else if (css.transform.startsWith("matrix3d(")) {
          const matrix = css.transform.slice(9, -1).split(",").map(Number);
          const axisAligned = new Set([0, 5, 10, 12, 13, 14, 15]);
          if (Math.abs(matrix[15] - 1) > .001 || matrix.some((value, i) => !axisAligned.has(i) && Math.abs(value) > .001)) return [];
        }
        if (ancestor === video) continue;
        // O overflow da raiz (e do body quando propagado) pertence ao viewport,
        // já limitado acima. Sua caixa DOM pode ter altura zero sem ocultar vídeo.
        if (ancestor === root || (ancestor === document.body && bodyOverflowOnViewport)) continue;
        const bounds = ancestor.getBoundingClientRect();
        const ax = bounds.width / (ancestor.offsetWidth || bounds.width);
        const ay = bounds.height / (ancestor.offsetHeight || bounds.height);
        const clipsX = css.overflowX !== "visible", clipsY = css.overflowY !== "visible";
        if (clipsX || clipsY) visible = clip(visible, {
          x: clipsX ? bounds.x + ancestor.clientLeft * ax : visible.x,
          y: clipsY ? bounds.y + ancestor.clientTop * ay : visible.y,
          width: clipsX ? ancestor.clientWidth * ax : visible.width,
          height: clipsY ? ancestor.clientHeight * ay : visible.height
        });
      }
      if (visible.width < 48 || visible.height < 32) return [];
      if (!ids.has(video)) ids.set(video, `${frameKey}:${++sequence}`);
      return [{...visible, id: ids.get(video), playing: !video.paused && !video.ended,
        label: String(video.getAttribute("aria-label") || video.title || "Vídeo").slice(0, 100)}];
    });
  }
  addEventListener("message", event => {
    if (event.data?.channel !== channel || !Array.isArray(event.data.videos)) return;
    // O offset pertence ao iframe concreto que enviou a mensagem.
    const iframe = [...document.querySelectorAll("iframe, frame")].find(item => item.contentWindow === event.source);
    if (!iframe) return;
    const rect = iframe.getBoundingClientRect();
    const sx = rect.width / (iframe.offsetWidth || rect.width);
    const sy = rect.height / (iframe.offsetHeight || rect.height);
    const box = {x: rect.x + iframe.clientLeft * sx, y: rect.y + iframe.clientTop * sy,
      width: iframe.clientWidth * sx, height: iframe.clientHeight * sy};
    const videos = event.data.videos.slice(0, 20).filter(item =>
      [item.x, item.y, item.width, item.height].every(Number.isFinite)
    ).map(item => clip({...item, x: box.x + item.x * sx, y: box.y + item.y * sy,
      width: item.width * sx, height: item.height * sy}, box));
    children.set(iframe, {time: performance.now(), videos});
  });
  function report() {
    let videos = localVideos();
    for (const [iframe, data] of children) {
      if (!iframe.isConnected || performance.now() - data.time > 700) { children.delete(iframe); continue; }
      videos.push(...data.videos);
    }
    videos = videos.map(item => clip(item, {x: 0, y: 0, width: innerWidth, height: innerHeight}))
      .filter(item => item.width >= 48 && item.height >= 32).slice(0, 20);
    if (window !== top) { parent.postMessage({channel, videos}, "*"); return; }
    try {
      chrome.runtime.sendMessage({type: "LAYLAY_STREAMING_LOCAL", videos,
        viewport: {outerWidth: number(outerWidth), outerHeight: number(outerHeight),
          innerWidth: number(innerWidth), innerHeight: number(innerHeight), dpr: number(devicePixelRatio)}}).catch(() => {});
    } catch (_) {} // Extensão recarregada: este documento antigo não tem autoridade.
  }
  setInterval(report, 200);
  addEventListener("resize", report);
  addEventListener("scroll", report, true);
  addEventListener("visibilitychange", report);
  report();
})();
