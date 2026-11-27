'use strict';

const LARGURA = 160;
const ALTURA = 110;
const RAD = Math.PI / 180;
const elementos = Object.fromEntries(
  [...document.querySelectorAll('[id]')].map(elemento => [elemento.id, elemento]),
);
const { arena, oled } = elementos;
const desenho = arena.getContext('2d');
const visor = oled.getContext('2d');
const modos = [...document.querySelectorAll('[data-modo]')];
const dicas = {
  pegar: 'Arraste a Laylay para pegar e solte para apoiar. Arraste o obstáculo para dentro do feixe.',
  girar: 'Arraste a caixa ou a alça da frente em torno do centro do corpo para girar.',
  inclinar: 'Arraste a caixa para os lados ou para cima e para baixo. Use Nivelar para voltar à posição inicial.',
};

let modo = 'pegar';
let cena = null;
let gesto = null;
let fila = null;
let geracao = 0;
let gravando = false;
let consultando = false;
let prazoEscrita = 0;
let ultimoEnvio = 0;
let quadroOled = '';
let inclinacaoVisual = null;
let quadroInclinacao = 0;
const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)');
let arquivoAberto = '';
let arquivosDisponiveis = [];
let carregandoArquivo = false;
let consultandoFirmware = false;
let enviandoFirmware = false;
let estadoFirmware = '';
let solicitacaoArquivo = 0;
let versaoFirmware = 0;
const arquivosEditados = new Map();

const seletorFirmware = elementos['arquivo-firmware'];
const editorFirmware = elementos['editor-firmware'];
const botaoAplicar = elementos['aplicar-firmware'];
const estadosFirmware = {
  pronto: ['ok', 'Pronto para editar.'],
  compilando: ['espera', 'Compilando a cópia da bancada…'],
  aplicado: ['ok', 'Firmware aplicado.'],
  erro: ['erro', 'A aplicação do firmware falhou. Confira a saída abaixo.'],
};

const limitar = (valor, minimo, maximo) => Math.min(maximo, Math.max(minimo, valor));
const normalizarAngulo = angulo => ((angulo % 360) + 540) % 360 - 180;
const numero = valor => typeof valor === 'number' && Number.isFinite(valor);
const graus = valor => numero(valor) ? `${Math.round(valor)}°` : '—';

function texto(elemento, valor) {
  if (elemento.textContent !== valor) elemento.textContent = valor;
}

function alterarConexao(estado, mensagem, aviso = '') {
  elementos.conexao.dataset.status = estado;
  texto(elementos['conexao-texto'], mensagem);
  elementos.aviso.hidden = !aviso;
  texto(elementos.aviso, aviso);
  elementos.nivelar.disabled = elementos.reiniciar.disabled = !cena || !!aviso;
}

async function requisitar(caminho, opcoes) {
  const resposta = await fetch(caminho, { cache: 'no-store', signal: AbortSignal.timeout(3000), ...opcoes });
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
  if (resposta.status === 204) return null;
  return resposta.json();
}

function aplicarEstado(estado, geracaoConsulta) {
  if (!estado?.corpo || !estado.obstaculo || !estado.firmware) return;
  if (!cena || (!gesto && !fila && geracaoConsulta === geracao)) {
    cena = estado;
  } else {
    cena = { ...cena, firmware: estado.firmware };
  }
  alterarConexao(cena.firmware.conectado ? 'ok' : 'espera',
    cena.firmware.conectado ? 'Laylay conectada' : 'Aguardando conexão da Laylay');
  atualizarLeituras();
  pintar();
}

async function consultar() {
  if (consultando || gravando || fila) return;
  consultando = true;
  const geracaoConsulta = geracao;
  try {
    aplicarEstado(await requisitar('/api/estado'), geracaoConsulta);
  } catch {
    alterarConexao('erro', 'Bancada sem conexão', 'Aguardando a conexão com a bancada local.');
  } finally {
    consultando = false;
  }
}

function enfileirar(mudanca) {
  if (!cena) return;
  ++geracao;
  if (mudanca.reset) {
    fila = { reset: true };
  } else {
    fila ??= {};
    for (const nome of ['corpo', 'obstaculo']) {
      if (!mudanca[nome]) continue;
      fila[nome] = { ...fila[nome], ...mudanca[nome] };
      Object.assign(cena[nome], mudanca[nome]);
    }
  }
  atualizarLeituras();
  pintar();
  agendarEscrita();
}

function agendarEscrita() {
  if (gravando || prazoEscrita || !fila) return;
  prazoEscrita = setTimeout(enviar, Math.max(0, 55 - (performance.now() - ultimoEnvio)));
}

async function enviar() {
  prazoEscrita = 0;
  if (gravando || !fila) return;
  gravando = true;
  ultimoEnvio = performance.now();
  const envio = fila;
  fila = null;
  const geracaoEnvio = geracao;
  try {
    aplicarEstado(await requisitar('/api/cena', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(envio),
    }), geracaoEnvio);
  } catch {
    alterarConexao('erro', 'Comando sem confirmação', 'A bancada não confirmou este movimento.');
    if (envio.corpo?.segurando === false && !fila && !gesto) {
      // Uma soltura perdida fica pendente até a próxima consulta bem-sucedida.
      cena.corpo.segurando = false;
      arena.dataset.soltar = 'sim';
    }
  } finally {
    gravando = false;
    agendarEscrita();
  }
}

function atualizarLeituras() {
  const { corpo, firmware } = cena;
  const { frente_mm, frente_estado, imu, protecao, pwm_esq, pwm_dir, ultima_linha } = firmware;
  texto(elementos.frente, numero(frente_mm) ? `${frente_mm} mm` : frente_estado === 'INVALIDA' ? 'Sem retorno' : frente_estado || '—');
  texto(elementos.imu, imu || '—');
  const fase = firmware.manuseio_fase;
  const nomesPostura = { LATERAL: 'De lado', EM_PE: 'Em pé', INVERTIDA: 'De ponta-cabeça',
    PROTESTO_LATERAL: 'Resmungando · de lado', PROTESTO_VERTICAL: 'Resmungando · em pé',
    PROTESTO_INVERTIDA: 'Resmungando · de ponta-cabeça' };
  texto(elementos['manuseio-fase'], nomesPostura[fase] || fase?.toLowerCase() || '—');
  texto(elementos.protecao, protecao || '—');
  elementos.frente.dataset.alerta = numero(frente_mm) && frente_mm <= 100 ? 'sim' : '';
  texto(elementos.pwm, numero(pwm_esq) && numero(pwm_dir) ? `${pwm_esq} · ${pwm_dir}` : '—');
  texto(elementos.ultima, ultima_linha || '—');
  for (const medida of ['yaw', 'roll', 'pitch']) texto(elementos[medida], graus(corpo[medida]));
  texto(elementos.apoio, corpo.segurando ? 'Em manuseio' : 'Apoiado');

  const dados = typeof firmware.oled === 'string' && /^[\da-f]{2048}$/i.test(firmware.oled) ? firmware.oled : '';
  oled.hidden = !dados;
  elementos['oled-vazio'].hidden = !!dados;
  if (dados === quadroOled) return;
  quadroOled = dados;
  if (!dados) return;
  const imagem = visor.createImageData(128, 64);
  for (let indice = 0; indice < 1024; ++indice) {
    const byte = parseInt(dados.slice(indice * 2, indice * 2 + 2), 16);
    for (let bit = 0; bit < 8; ++bit) {
      const posicao = (indice * 8 + bit) * 4;
      const aceso = byte & (128 >> bit);
      imagem.data.set(aceso ? [165, 255, 223, 255] : [7, 20, 22, 255], posicao);
    }
  }
  visor.putImageData(imagem, 0, 0);
}

function linha(x, y, fimX, fimY) {
  desenho.beginPath();
  desenho.moveTo(x, y);
  desenho.lineTo(fimX, fimY);
  desenho.stroke();
}

function pintarGrade() {
  desenho.fillStyle = '#0e1a1d';
  desenho.fillRect(0, 0, LARGURA, ALTURA);
  desenho.lineWidth = .12;
  for (let x = 0; x <= LARGURA; x += 5) {
    desenho.strokeStyle = x % 20 === 0 ? '#375057' : '#23353a';
    linha(x, 0, x, ALTURA);
  }
  for (let y = 0; y <= ALTURA; y += 5) {
    desenho.strokeStyle = y % 20 === 0 ? '#375057' : '#23353a';
    linha(0, y, LARGURA, y);
  }
  desenho.fillStyle = '#91aeb1';
  desenho.font = '2.2px Consolas, monospace';
  for (let x = 20; x < LARGURA; x += 20) desenho.fillText(`${x}`, x + 1, 4);
  for (let y = 20; y < ALTURA; y += 20) desenho.fillText(`${y}`, 1.25, y + 3.2);
  desenho.fillText('cm', 2, 4);
  desenho.strokeStyle = '#a4c3c3';
  desenho.lineWidth = .3;
  linha(5, 103, 15, 103);
  linha(5, 101.8, 5, 104.2);
  linha(15, 101.8, 15, 104.2);
  desenho.fillText('10 cm', 6, 107);
}

function pintarFeixe(corpo, firmware) {
  const angulo = corpo.yaw * RAD;
  const dx = Math.sin(angulo);
  const dy = -Math.cos(angulo);
  const inicioX = corpo.x + dx * 9;
  const inicioY = corpo.y + dy * 9;
  const mediu = numero(firmware.frente_mm);
  const alcance = mediu ? firmware.frente_mm / 10 : 65;
  const fimX = inicioX + dx * alcance;
  const fimY = inicioY + dy * alcance;
  desenho.beginPath();
  desenho.moveTo(inicioX, inicioY);
  desenho.lineTo(fimX + dy * 3, fimY - dx * 3);
  desenho.lineTo(fimX - dy * 3, fimY + dx * 3);
  desenho.closePath();
  desenho.fillStyle = mediu && alcance <= 10 ? '#f5b36a32' : '#86e9d01e';
  desenho.fill();
  desenho.strokeStyle = mediu && alcance <= 10 ? '#ffd48e' : '#92daca';
  desenho.lineWidth = mediu ? .37 : .22;
  desenho.setLineDash(mediu ? [] : [1.1, 1.3]);
  linha(inicioX, inicioY, fimX, fimY);
  desenho.setLineDash([]);
}

function caixa(x, y, w, h, raio, preenchimento, borda) {
  desenho.beginPath();
  desenho.roundRect(x, y, w, h, raio);
  desenho.fillStyle = preenchimento;
  desenho.fill();
  desenho.strokeStyle = borda;
  desenho.stroke();
}

function desenharFace(vertices, cor, borda) {
  desenho.beginPath();
  desenho.moveTo(vertices[0][0], vertices[0][1]);
  for (const [x, y] of vertices.slice(1)) desenho.lineTo(x, y);
  desenho.closePath();
  desenho.fillStyle = cor;
  desenho.fill();
  desenho.strokeStyle = borda;
  desenho.stroke();
}

function pintarCorpo(corpo, firmware, pose) {
  desenho.save();
  desenho.translate(corpo.x, corpo.y);
  desenho.rotate(corpo.yaw * RAD);
  desenho.lineWidth = .3;
  desenho.strokeStyle = '#e2b576';
  if (corpo.segurando) {
    desenho.setLineDash([1, .9]);
    desenho.strokeRect(-11, -11, 22, 22);
    desenho.setLineDash([]);
  }
  const r = pose.roll * RAD;
  const p = pose.pitch * RAD;
  const sr = Math.sin(r), cr = Math.cos(r), sp = Math.sin(p), cp = Math.cos(p);
  const altura = Math.abs(sr) * 6 + Math.abs(sp) * 6 + (corpo.segurando ? 1.5 : 0);
  function projetar(x, y, z) {
    const rz = x * sr + z * cr;
    const rx = x * cr - z * sr;
    const ry = y * cp + rz * sp;
    const az = -y * sp + rz * cp + altura;
    return [rx + az * .23, ry - az * .37, az - rx * .23 + ry * .37];
  }
  desenho.beginPath();
  desenho.ellipse(-altura * .13, altura * .2, 9.7, 10.1, 0, 0, Math.PI * 2);
  desenho.fillStyle = '#070e13a6';
  desenho.fill();
  const inclinado = Math.max(Math.abs(pose.roll), Math.abs(pose.pitch)) >= 14;
  const frente = inclinado ? '#ffd48e' : '#a3f6d7';
  const borda = inclinado ? '#d6a968' : '#86c8ba';
  const vertices = [[-7,-9,2],[7,-9,2],[7,9,2],[-7,9,2],[-7,-9,-2],[7,-9,-2],[7,9,-2],[-7,9,-2]]
    .map(v => projetar(...v));
  const faces = [
    [[0,1,2,3], '#294f51'], [[4,7,6,5], '#18292f'],
    [[0,4,5,1], '#366468'], [[1,5,6,2], '#204046'],
    [[2,6,7,3], '#182f36'], [[3,7,4,0], '#2b5558'],
  ].map(([ids, cor], indice) => {
    const pontos = ids.map(i => vertices[i]);
    const [a,b,c] = pontos;
    return { pontos, cor, indice, visivel: (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]) > .03,
      profundidade: pontos.reduce((total, p) => total + p[2], 0) / 4 };
  }).filter(face => face.visivel).sort((a,b) => a.profundidade - b.profundidade);

  function noPlano(z, desenhar) {
    const o = projetar(0,0,z), x = projetar(1,0,z), y = projetar(0,1,z);
    desenho.save();
    desenho.transform(x[0]-o[0], x[1]-o[1], y[0]-o[0], y[1]-o[1], o[0], o[1]);
    desenhar();
    desenho.restore();
  }
  noPlano(-.5, () => {
    for (const [x, pwm] of [[-9.2, firmware.pwm_esq], [6.6, firmware.pwm_dir]]) {
      desenho.lineWidth = .28;
      caixa(x, -5.6, 2.6, 11.2, .65, pwm ? '#6cae9a' : '#0a1419', '#7e9a9f');
      desenho.strokeStyle = pwm ? '#a9f8dc' : '#59727a';
      desenho.lineWidth = .16;
      for (let marca = -4; marca <= 4; marca += 2) linha(x+.35, marca, x+2.25, marca);
    }
  });
  for (const face of faces) {
    desenho.lineWidth = .3;
    desenharFace(face.pontos, face.cor, borda);
    if (face.indice === 0) noPlano(2, () => {
      desenho.lineWidth = .22;
      caixa(-5.4, -5.4, 10.8, 5.7, .65, '#09181b', '#72a498');
      if (quadroOled) desenho.drawImage(oled, -4.9, -5.25, 9.8, 4.9);
      desenho.fillStyle = frente;
      desenho.font = 'bold 1.55px Consolas, monospace';
      desenho.textAlign = 'center';
      desenho.fillText('LAYLAY', 0, 5.8);
      desenho.fillRect(-4.6, -9, 9.2, .58);
    });
  }
  if (cr * cp < 0) {
    desenho.fillStyle = frente;
    desenho.font = 'bold 1.8px Consolas, monospace';
    desenho.textAlign = 'center';
    desenho.fillText('VIRADA', 0, 13);
  }
  desenho.fillStyle = frente;
  desenho.beginPath();
  desenho.moveTo(0, -11.6);
  desenho.lineTo(-1.3, -9.7);
  desenho.lineTo(1.3, -9.7);
  desenho.fill();
  if (modo === 'girar') {
    desenho.strokeStyle = frente;
    linha(0, -12, 0, -15);
    desenho.beginPath();
    desenho.arc(0, -16.5, 1.5, 0, 2*Math.PI);
    desenho.stroke();
  }
  desenho.restore();
}

function pintarObstaculo(objeto) {
  const { x, y, raio } = objeto;
  desenho.save();
  desenho.beginPath();
  desenho.arc(x, y, raio, 0, 2*Math.PI);
  desenho.fillStyle = '#654630';
  desenho.fill();
  desenho.clip();
  desenho.strokeStyle = '#9c6c43';
  desenho.lineWidth = .7;
  for (let d = -2*raio; d <= 2*raio; d += 2) linha(x-raio+d, y+raio, x+raio+d, y-raio);
  desenho.restore();
  desenho.beginPath();
  desenho.arc(x, y, raio, 0, 2*Math.PI);
  desenho.strokeStyle = '#ffc780';
  desenho.lineWidth = .4;
  desenho.stroke();
  desenho.fillStyle = '#ffedcf';
  desenho.font = '2.15px Consolas, monospace';
  desenho.textAlign = 'center';
  desenho.fillText('OBSTÁCULO', x, limitar(y + raio + 3.5, 5, ALTURA-2));
  desenho.textAlign = 'start';
}

function pintar() {
  if (quadroInclinacao) cancelAnimationFrame(quadroInclinacao);
  quadroInclinacao = 0;
  desenho.setTransform(arena.width / LARGURA, 0, 0, arena.height / ALTURA, 0, 0);
  pintarGrade();
  if (!cena) return;
  pintarFeixe(cena.corpo, cena.firmware);
  pintarObstaculo(cena.obstaculo);
  const agora = performance.now();
  const { roll, pitch } = cena.corpo;
  if (!inclinacaoVisual || reduzirMovimento.matches) inclinacaoVisual = { roll, pitch, t: agora };
  const dt = limitar(agora - inclinacaoVisual.t, 0, 80);
  inclinacaoVisual.t = agora;
  const fator = 1 - Math.exp(-dt / 52);
  for (const eixo of ['roll', 'pitch']) {
    const delta = cena.corpo[eixo] - inclinacaoVisual[eixo];
    inclinacaoVisual[eixo] += Math.abs(delta) < .12 ? delta : delta * fator;
  }
  pintarCorpo(cena.corpo, cena.firmware, inclinacaoVisual);
  if (inclinacaoVisual.roll !== roll || inclinacaoVisual.pitch !== pitch) {
    quadroInclinacao = requestAnimationFrame(pintar);
  }
}

function redimensionar() {
  const escala = Math.min(window.devicePixelRatio || 1, 3);
  arena.width = Math.max(1, Math.round(arena.clientWidth * escala));
  arena.height = Math.max(1, Math.round(arena.clientHeight * escala));
  pintar();
}

function pontoNaArena(evento) {
  const area = arena.getBoundingClientRect();
  return { x: (evento.clientX - area.left) * LARGURA / area.width,
    y: (evento.clientY - area.top) * ALTURA / area.height };
}

function alvoNoPonto(ponto) {
  if (!cena) return '';
  const { corpo, obstaculo } = cena;
  if (Math.hypot(obstaculo.x - ponto.x, obstaculo.y - ponto.y) <= obstaculo.raio + 1) return 'obstaculo';
  const dx = ponto.x - corpo.x;
  const dy = ponto.y - corpo.y;
  const angulo = corpo.yaw * RAD;
  const x = dx * Math.cos(angulo) + dy * Math.sin(angulo);
  const y = dy * Math.cos(angulo) - dx * Math.sin(angulo);
  if (modo === 'girar' && Math.hypot(x, y + 16.5) <= 3) return 'corpo';
  return Math.abs(x) <= 10 && Math.abs(y) <= 11 ? 'corpo' : '';
}

function anguloEmTorno(ponto, centro) {
  return Math.atan2(ponto.x - centro.x, centro.y - ponto.y) / RAD;
}

function comecarGesto(evento) {
  if (gesto || (evento.button !== 0 && evento.pointerType === 'mouse')) return;
  const ponto = pontoNaArena(evento);
  const alvo = alvoNoPonto(ponto);
  if (!alvo) return;
  const inicial = { ...cena[alvo] };
  gesto = { id: evento.pointerId, alvo, modo, ponto, inicial };
  arena.focus({ preventScroll: true });
  arena.setPointerCapture(evento.pointerId);
  arena.dataset.puxando = 'sim';
  if (alvo === 'corpo') enfileirar({ corpo: { segurando: true } });
}

function moverGesto(evento) {
  const ponto = pontoNaArena(evento);
  arena.dataset.alvo = alvoNoPonto(ponto) ? 'sim' : '';
  if (!gesto || gesto.id !== evento.pointerId) return;
  const { alvo, inicial, ponto: origem } = gesto;
  const dx = ponto.x - origem.x;
  const dy = ponto.y - origem.y;
  if (alvo === 'obstaculo' || gesto.modo === 'pegar') {
    const margem = alvo === 'obstaculo' ? inicial.raio : 11;
    enfileirar({ [alvo]: { x: limitar(inicial.x + dx, margem, LARGURA-margem),
      y: limitar(inicial.y + dy, margem, ALTURA-margem) } });
  } else if (gesto.modo === 'girar') {
    const delta = Math.hypot(origem.x-inicial.x, origem.y-inicial.y) < 2
      ? dx * 5 : anguloEmTorno(ponto, inicial) - anguloEmTorno(origem, inicial);
    enfileirar({ corpo: { yaw: normalizarAngulo(inicial.yaw + delta) } });
  } else {
    enfileirar({ corpo: { roll: limitar(inicial.roll + dx*3.5, -180, 180),
      pitch: limitar(inicial.pitch - dy*3.5, -180, 180) } });
  }
}

function encerrarGesto(evento) {
  if (!gesto || (evento && gesto.id !== evento.pointerId)) return;
  const { alvo, id } = gesto;
  gesto = null;
  arena.dataset.puxando = '';
  if (arena.hasPointerCapture(id)) arena.releasePointerCapture(id);
  if (alvo === 'corpo') enfileirar({ corpo: { segurando: false } });
}

function selecionarModo(valor) {
  modo = valor;
  for (const botao of modos) botao.setAttribute('aria-pressed', String(botao.dataset.modo === modo));
  texto(elementos.dica, dicas[modo]);
  pintar();
}

function interagirComTeclado(evento) {
  if (evento.altKey || evento.metaKey || evento.ctrlKey) return;
  const escolha = { '1': 'pegar', '2': 'girar', '3': 'inclinar' }[evento.key];
  if (escolha) {
    selecionarModo(escolha);
    return;
  }
  if (!cena || gesto) return;
  const { corpo, obstaculo } = cena;
  if (evento.key.toLowerCase() === 'n') {
    nivelar();
    return;
  }
  if (evento.key === ' ' || evento.key === 'Escape') {
    evento.preventDefault();
    if (!evento.repeat) enfileirar({ corpo: { segurando: evento.key === ' ' && !corpo.segurando } });
    return;
  }
  const dx = { ArrowLeft: -1, ArrowRight: 1 }[evento.key] || 0;
  const dy = { ArrowUp: -1, ArrowDown: 1 }[evento.key] || 0;
  if (!dx && !dy) return;
  evento.preventDefault();
  if (evento.shiftKey || modo === 'pegar') {
    const alvo = evento.shiftKey ? 'obstaculo' : 'corpo';
    const posicao = evento.shiftKey ? obstaculo : corpo;
    const margem = evento.shiftKey ? obstaculo.raio : 11;
    enfileirar({ [alvo]: { x: limitar(posicao.x + dx*3, margem, LARGURA-margem),
      y: limitar(posicao.y + dy*3, margem, ALTURA-margem) } });
  } else if (modo === 'girar') {
    enfileirar({ corpo: { yaw: normalizarAngulo(corpo.yaw + (dx || dy)*8) } });
  } else {
    enfileirar({ corpo: { roll: limitar(corpo.roll + dx*5, -180, 180),
      pitch: limitar(corpo.pitch - dy*5, -180, 180) } });
  }
}

function nivelar() {
  enfileirar({ corpo: { roll: 0, pitch: 0, segurando: false } });
}

function selecionarVista(vista) {
  const editorAberto = vista === 'editor';
  elementos['vista-arena'].hidden = editorAberto;
  elementos['vista-editor'].hidden = !editorAberto;
  document.querySelector('main').dataset.vista = vista;
  elementos['abrir-arena'].setAttribute('aria-pressed', String(!editorAberto));
  elementos['abrir-editor'].setAttribute('aria-pressed', String(editorAberto));
  if (editorAberto) acompanharFirmware();
}

function mensagemFirmware(status, mensagem) {
  elementos['estado-firmware'].dataset.status = status;
  texto(elementos['estado-firmware'], mensagem);
}

function atualizarEditor() {
  const editado = arquivosEditados.get(arquivoAberto);
  editorFirmware.disabled = carregandoArquivo || enviandoFirmware || !editado;
  seletorFirmware.disabled = enviandoFirmware || arquivosDisponiveis.length === 0;
  botaoAplicar.disabled = editorFirmware.disabled || estadoFirmware === 'compilando';
  elementos['rascunho-firmware'].hidden = !editado || editado.conteudo === editado.salvo;
}

function aplicarEstadoFirmware(dados) {
  if (!dados) return;
  if (Array.isArray(dados.arquivos)) {
    arquivosDisponiveis = dados.arquivos;
    if (seletorFirmware.options.length !== arquivosDisponiveis.length ||
        arquivosDisponiveis.some((nome, i) => seletorFirmware.options[i]?.value !== nome)) {
      seletorFirmware.replaceChildren(...arquivosDisponiveis.map(nome => new Option(nome, nome)));
      if (arquivosDisponiveis.includes(arquivoAberto)) seletorFirmware.value = arquivoAberto;
    }
    if (!arquivosDisponiveis.includes(arquivoAberto) && arquivosDisponiveis.length) {
      seletorFirmware.value = arquivosDisponiveis.find(nome => nome.endsWith('.ino')) ?? arquivosDisponiveis[0];
      abrirArquivo(seletorFirmware.value);
    } else if (arquivoAberto && !carregandoArquivo && !arquivosEditados.has(arquivoAberto)) {
      abrirArquivo(arquivoAberto);
    }
  }
  if (typeof dados.log === 'string') texto(elementos['log-firmware'], dados.log || '—');
  if (Object.hasOwn(estadosFirmware, dados.estado)) {
    if (dados.estado === 'erro' && estadoFirmware !== 'erro') elementos['detalhes-firmware'].open = true;
    estadoFirmware = dados.estado;
    mensagemFirmware(...estadosFirmware[estadoFirmware]);
  }
  atualizarEditor();
}

async function acompanharFirmware() {
  if (consultandoFirmware || enviandoFirmware) return;
  consultandoFirmware = true;
  const versao = versaoFirmware;
  try {
    const resposta = await requisitar('/api/firmware');
    if (versao === versaoFirmware) aplicarEstadoFirmware(resposta);
  } catch {
    if (versao === versaoFirmware) mensagemFirmware('erro', 'Não consegui consultar o editor de firmware.');
  } finally {
    consultandoFirmware = false;
  }
}

async function abrirArquivo(nome) {
  const solicitacao = ++solicitacaoArquivo;
  arquivoAberto = nome;
  editorFirmware.value = '';
  carregandoArquivo = true;
  atualizarEditor();
  try {
    if (!arquivosEditados.has(nome)) {
      const dados = await requisitar(`/api/firmware?arquivo=${encodeURIComponent(nome)}`);
      if (dados.arquivo !== nome || typeof dados.conteudo !== 'string') throw new Error('Arquivo inválido');
      arquivosEditados.set(nome, { conteudo: dados.conteudo, salvo: dados.conteudo });
    }
    if (solicitacao === solicitacaoArquivo) editorFirmware.value = arquivosEditados.get(nome).conteudo;
  } catch {
    if (solicitacao === solicitacaoArquivo) mensagemFirmware('erro', `Não consegui abrir ${nome}.`);
  } finally {
    if (solicitacao === solicitacaoArquivo) {
      carregandoArquivo = false;
      atualizarEditor();
    }
  }
}

async function salvarEAplicar() {
  if (botaoAplicar.disabled) return;
  const nome = arquivoAberto;
  const arquivo = arquivosEditados.get(nome);
  ++versaoFirmware;
  enviandoFirmware = true;
  atualizarEditor();
  mensagemFirmware('espera', 'Salvando a cópia da bancada…');
  try {
    await requisitar(`/api/firmware?arquivo=${encodeURIComponent(nome)}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conteudo: arquivo.conteudo }),
    });
    arquivo.salvo = arquivo.conteudo;
    await requisitar('/api/compilar', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
    });
    estadoFirmware = 'compilando';
    mensagemFirmware(...estadosFirmware.compilando);
  } catch {
    mensagemFirmware('erro', 'A bancada não confirmou o salvamento e a aplicação.');
  } finally {
    enviandoFirmware = false;
    atualizarEditor();
  }
}

for (const botao of modos) botao.addEventListener('click', () => selecionarModo(botao.dataset.modo));
elementos.nivelar.addEventListener('click', nivelar);
elementos.reiniciar.addEventListener('click', () => enfileirar({ reset: true }));
elementos['abrir-arena'].addEventListener('click', () => selecionarVista('arena'));
elementos['abrir-editor'].addEventListener('click', () => selecionarVista('editor'));
seletorFirmware.addEventListener('change', () => abrirArquivo(seletorFirmware.value));
editorFirmware.addEventListener('input', () => {
  const editado = arquivosEditados.get(arquivoAberto);
  if (editado) editado.conteudo = editorFirmware.value;
  atualizarEditor();
});
editorFirmware.addEventListener('keydown', evento => {
  if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === 's') {
    evento.preventDefault();
    salvarEAplicar();
  }
});
botaoAplicar.addEventListener('click', salvarEAplicar);
arena.addEventListener('pointerdown', comecarGesto);
arena.addEventListener('pointermove', moverGesto);
for (const evento of ['pointerup', 'pointercancel', 'lostpointercapture']) arena.addEventListener(evento, encerrarGesto);
arena.addEventListener('keydown', interagirComTeclado);
window.addEventListener('blur', () => encerrarGesto());
window.addEventListener('pagehide', () => {
  if (gesto?.alvo !== 'corpo' && !cena?.corpo.segurando) return;
  navigator.sendBeacon('/api/cena', new Blob(['{"corpo":{"segurando":false}}'], { type: 'application/json' }));
});
new ResizeObserver(redimensionar).observe(arena);

alterarConexao('espera', 'Conectando ao firmware');
consultar();
setInterval(() => {
  if (arena.dataset.soltar && !gesto && !fila && !gravando && elementos.conexao.dataset.status !== 'erro') {
    delete arena.dataset.soltar;
    enfileirar({ corpo: { segurando: false } });
  }
  consultar();
}, 230);
setInterval(() => {
  if (estadoFirmware === 'compilando' || !elementos['vista-editor'].hidden) acompanharFirmware();
}, 1200);
