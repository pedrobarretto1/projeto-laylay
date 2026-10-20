// Estudo somente leitura do bundle: navegação local e medidas, sem ações de domínio.
// Executar em sessão isolada agent-browser sobre o index.html de produção.
(async () => {
  const ui = window.LaylayInterface;
  ui.request = async () => ''; // Nenhum pedido deste estudo alcança um executor.
  const paint = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const visible = el => {
    const rect = el.getBoundingClientRect(), style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const box = el => {
    if (!el) return null;
    const rect = el.getBoundingClientRect(), css = getComputedStyle(el);
    return {text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 85),
      x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height),
      font: css.fontFamily, size: css.fontSize, lineHeight: css.lineHeight, color: css.color,
      background: css.backgroundColor, radius: css.borderRadius};
  };
  const report = {viewport: [innerWidth, innerHeight], origem: 'bundle local, estado inicial sem ponte; nenhuma habilidade executada', abas: []};
  for (const name of ['home', 'chat', 'lamp', 'music', 'streaming', 'memory', 'system', 'dev', 'settings']) {
    ui.goPage(name);
    await paint();
    const page = document.getElementById('page-content');
    page.scrollTop = 0;
    const elements = [...page.querySelectorAll('*')].filter(visible);
    const leafText = elements.filter(el => el.childElementCount === 0 && el.textContent.trim());
    const buttons = [...page.querySelectorAll('button,input,select')].filter(visible);
    report.abas.push({name, title: document.querySelector('.page-heading h2')?.textContent,
      page: box(page), contentHeight: page.scrollHeight, viewportHeight: page.clientHeight,
      sections: [...page.querySelectorAll('h3')].map(el => box(el)),
      textBelow12px: leafText.filter(el => parseFloat(getComputedStyle(el).fontSize) < 12).length,
      textElements: leafText.length,
      fontSizes: [...new Set(leafText.map(el => getComputedStyle(el).fontSize))].sort((a,b) => parseFloat(a) - parseFloat(b)),
      actions: buttons.map(box),
      smallTargets: buttons.filter(el => {const rect=el.getBoundingClientRect();return rect.width<32 || rect.height<32;}).map(box),
      nestedScrollers: elements.filter(el => el.scrollHeight > el.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(el).overflowY)).map(box),
      bottom: ''});
    page.scrollTop = page.scrollHeight;
    await paint();
    report.abas.at(-1).bottom = page.innerText.slice(-1000);
  }
  for (const mode of ['quick', 'island']) {
    ui.goMode(mode);await paint();
    report[mode] = {root: box(document.querySelector(mode === 'quick' ? '.quick-window' : '.island')),
      actions: [...document.querySelectorAll('#workspace button,#workspace input')].filter(visible).map(box)};
  }
  ui.goMode('full');ui.goPage('home');
  return JSON.stringify(report);
})()
