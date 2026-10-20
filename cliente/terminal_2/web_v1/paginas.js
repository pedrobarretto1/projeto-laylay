/* Páginas oficiais: apenas projeções públicas e pedidos aos owners existentes. */
(() => {
  'use strict';
  const p = window.LaylayInterface;
  if (!p) return;
  const s = p.state, esc = p.escapeHTML, ico = p.icon;
  const ui = {
    playlist: '', detail: null, catalog: '', trackQuery: '', all: false,
    lyrics: false, memoryQuery: '', memoryCategory: '', provider: '', models: {},
    settingsDirty: false, credentialAction: 'preserve', settingsMessage: '', legacyMascot: false,
    pending: new Map(), requests: new Map(), finished: new Map(), history: {}, lastSamples: {},
    devCategory: 'ALL', devLevel: 'normal', devPaused: false, devEvents: [],
    devBody: {}, devOutput: [], devCommand: '', detailMessage: '', musicMeter: null,
  };
  const obj = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const list = value => Array.isArray(value) ? value : [];
  const show = value => value === null || value === undefined || value === '' ? '—' : String(value);
  const text = value => esc(show(value));
  const number = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
  const percent = value => number(value) === null ? '—' : `${Math.round(value)}%`;
  const stamp = value => number(value) && value > 0 ? new Date(value * 1000).toLocaleTimeString('pt-BR') : '—';
  const duration = value => number(value) === null || value < 0 ? '—' : `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, '0')}`;
  const fresh = value => ({fresh:'Atual', stale:'Leitura anterior', unavailable:'Indisponível'})[value] || '—';
  const music = () => obj(obj(s.dashboard).music);
  const disabled = enabled => enabled ? '' : ' disabled';
  const busy = key => ui.pending.has(key);
  const invalidate = () => typeof p.invalidate==='function'?p.invalidate():p.render();
  let meterExpiry=0;
  const button = (label, action, attrs = '', enabled = true, style = '') => `<button class="tp-button ${style}" data-tp-action="${action}"${disabled(enabled)} ${attrs}>${label}</button>`;
  const empty = message => `<div class="tp-empty">${esc(message)}</div>`;
  const note = message => `<div class="tp-note">${esc(message)}</div>`;
  const kv = (label, value) => `<div class="tp-kv"><span>${esc(label)}</span><span>${value}</span></div>`;
  const section = (title, body, subtitle = '', extra = '') => `<section class="tp-section"><div class="tp-head"><div><h3>${esc(title)}</h3>${subtitle ? `<p>${esc(subtitle)}</p>` : ''}</div>${extra}</div>${body}</section>`;
  const wrap = (eyebrow, title, subtitle, body) => `<div class="tp-root">${p.pageHeading(eyebrow, title, subtitle)}${body}</div>`;
  const search = (field, value, placeholder) => `<label class="tp-search">${ico('search')}<input data-tp-input="${field}" data-field="tp-${field}" value="${esc(value)}" placeholder="${esc(placeholder)}" aria-label="${esc(placeholder)}"></label>`;
  function artwork(url, size = '', title = '') {
    const safe = /^https:\/\/i\.ytimg\.com\/vi\/[A-Za-z0-9_-]{11}\/(?:mqdefault|hqdefault|maxresdefault)\.jpg$/.test(url || '') || /^laylay-playlist-artwork:\/\/[a-f0-9]{24}\.png$/.test(url || '');
    return `<div class="tp-art ${size}" aria-hidden="true">${safe ? `<img src="${esc(url)}" alt="" style="width:100%;height:100%;object-fit:cover;position:relative">` : `<span>${esc(title ? title.slice(0, 1) : '♪')}</span>`}</div>`;
  }
  function meter(label, value, color) {
    const v = number(value);
    return `<div><div class="tp-stat-label"><span>${esc(label)}</span><span>${percent(v)}</span></div><div class="tp-meter"><i style="width:${v === null ? 0 : Math.max(0, Math.min(100, v))}%;background:${color}"></i></div></div>`;
  }
  async function request(kind, data, key = kind) {
    if (busy(key)) return '';
    const waiting = {};
    ui.pending.set(key, waiting);
    let id = '';
    try { id = await p.request(kind, data); }
    catch (_error) { p.toast('A ponte não confirmou o envio.'); }
    if (!id) { if(ui.pending.get(key)===waiting)ui.pending.delete(key); p.toast('Pedido não enviado. Verifique a conexão.'); }
    else if (ui.finished.has(id)) {
      // Um receipt pode chegar pelo sinal antes da resposta assíncrona do slot.
      const result=ui.finished.get(id);ui.finished.delete(id);
      if(ui.pending.get(key)===waiting)ui.pending.delete(key);
      if(kind==='playlist'&&data.operation!=='detail'&&obj(result.result).ok&&data.playlist===ui.playlist)detail();
    } else if(ui.pending.get(key)===waiting) {
      ui.pending.set(key, id);
      // Nunca conservar o payload de configuração: ele pode conter uma chave.
      ui.requests.set(id, {key, kind, query:data.query, playlist:data.playlist});
    }
    invalidate();
    return id;
  }
  const action = (id, requestText, payload = {}) => request('acao', {action:id, request:requestText, payload}, id);
  function playlist(operation, extra = {}) {
    return request('playlist', {operation, playlist:ui.playlist, ...extra}, 'playlist');
  }
  function detail(offset = 0) {
    if (!ui.playlist) return;
    if (!offset) ui.detail = null;
    ui.detailMessage = 'Carregando faixas…';
    return playlist('detail', {query:ui.trackQuery, offset, limit:50});
  }
  function dialog(title, body, submitLabel, callback, dangerous = false) {
    document.getElementById('tp-dialog')?.remove();
    const element = document.createElement('dialog');
    element.id = 'tp-dialog'; element.className = 'tp-root';
    element.style.cssText = 'max-width:520px;width:calc(100% - 36px);background:#191e27;color:#e7eaf0;border:1px solid #494154;border-radius:16px;padding:24px;box-shadow:0 30px 100px #0009';
    element.innerHTML = `<form><h3 style="font-size:21px;margin-bottom:16px">${esc(title)}</h3>${body}<div class="tp-actions tp-gap" style="justify-content:flex-end"><button class="tp-button" type="button" data-cancel>Cancelar</button><button class="tp-button ${dangerous?'tp-danger':'active'}" type="submit">${esc(submitLabel)}</button></div></form>`;
    element.querySelector('[data-cancel]').onclick = () => element.close();
    element.addEventListener('close', () => element.remove(), {once:true});
    element.querySelector('form').addEventListener('submit', event => {
      event.preventDefault(); const values = new FormData(event.target); element.close(); callback(values);
    });
    document.body.append(element); element.showModal();
  }
  function player() {
    const m = music(), ready = s.connected && m.controls_available === true, playing = m.state === 'playing';
    const progress = number(m.duration_seconds) && number(m.position_seconds) !== null ? Math.min(100, m.position_seconds / m.duration_seconds * 100) : 0;
    return `<section class="tp-player ${playing&&m.freshness==='fresh'?'is-playing':''}"><div class="tp-player-top">${artwork(m.artwork_url,'large',m.title)}<div class="tp-player-copy"><div class="eyebrow">${esc(({playing:'Tocando agora',paused:'Em pausa',ended:'Finalizada'})[m.state] || 'Aguardando reprodução')} · ${fresh(m.freshness)}</div><h2>${text(m.title)}</h2><p>${text(m.channel)}</p><small>${text(m.playlist)}</small><div class="tp-controls">${button(ico('prev'),'media-previous','aria-label="Faixa anterior"',ready&&!busy('media_previous'))}${button(ico(playing?'pause':'play'),'media-toggle',`aria-label="${playing?'Pausar':'Reproduzir'}"`,ready&&!busy('media_toggle'),'tp-primary-play')}${button(ico('next'),'media-next','aria-label="Próxima faixa"',ready&&!busy('media_next'))}${button('⇄','shuffle',`aria-label="Aleatório da playlist"`,s.connected&&m.shuffle_available===true&&!busy('playlist_shuffle'))}${button('↻','repeat',`aria-label="Repetir faixa" aria-pressed="${m.repeat_enabled===true}"`,s.connected&&m.repeat_available===true&&!busy('media_repeat'),m.repeat_enabled?'active':'')}${button('Recomeçar','replay','',s.connected&&m.replay_available===true&&!busy('media_replay'))}</div></div></div>${playbackMeter()}<div class="tp-progress" role="progressbar" aria-label="Progresso observado da faixa" aria-valuenow="${Math.round(progress)}" aria-valuemin="0" aria-valuemax="100"><span style="width:${progress}%"></span></div><div class="tp-times"><span>${duration(m.position_seconds)}</span><span>${duration(m.duration_seconds)}</span></div><div class="tp-volume">${ico('volume')}<span>Volume mestre</span><input type="range" min="0" max="100" value="${number(m.volume_percent)??0}" data-tp-change="volume" aria-label="Volume mestre"${disabled(s.connected&&number(m.volume_percent)!==null&&!busy('volume_set'))}><output data-tp-volume>${percent(m.volume_percent)}</output></div>${m.muted?note('O player está mudo.'):''}</section>`;
  }
  function meterProjection() {
    const m=music(), meter=ui.musicMeter;
    const playing=s.connected&&m.state==='playing'&&m.freshness==='fresh';
    const measured=playing&&meter?.video_id===m.video_id&&Date.now()/1000-meter.observed_at<2;
    return {playing,measured,levels:measured&&!s.preferences.reduced?meter.levels:[0,0,0]};
  }
  function playbackMeter() {
    const {playing,measured,levels}=meterProjection();
    return `<div class="tp-playback-strip" data-render-key="playback-meter"><div class="tp-wave" data-music-meter role="img" aria-label="${measured?'Medidor observado de três bandas':'Sem medição de áudio atual'}" data-playing="${playing}">${Array.from({length:24},(_,i)=>`<i style="height:${4+levels[i%3]*24}px"></i>`).join('')}</div><small data-meter-caption>${playing?(measured?'Áudio observado · 3 bandas':'Reprodução observada · aguardando medidor'):'Reprodução em espera'}</small></div>`;
  }
  function updateMeter() {
    const {playing,measured,levels}=meterProjection();
    for(const element of document.querySelectorAll('[data-music-meter]')) {
      element.dataset.playing=String(playing);
      element.setAttribute('aria-label',measured?'Medidor observado de três bandas':'Sem medição de áudio atual');
      element.querySelectorAll('i').forEach((bar,index)=>{bar.style.height=`${4+levels[index%3]*24}px`;});
    }
    for(const caption of document.querySelectorAll('[data-meter-caption]'))caption.textContent=playing?(measured?'Áudio observado · 3 bandas':'Reprodução observada · aguardando medidor'):'Reprodução em espera';
  }
  function queue() {
    const m = music();
    const rows = list(m.queue).map((item,index) => ({item,index})).filter(({item}) => item.item_id !== m.video_id);
    return section('Próximas faixas', rows.map(({item,index}, position) => `<div class="tp-queue"><small>${String(position+1).padStart(2,'0')}</small>${artwork(item.artwork_url,'small',item.title)}<button class="tp-track-copy" data-tp-action="queue" data-index="${index}"${disabled(s.connected&&m.queue_freshness==='fresh'&&!!item.item_id&&!busy('queue_play'))}><strong>${text(item.title)}</strong><small>${text(item.channel)}</small></button><small>${duration(item.duration_seconds)}</small>${button(ico('play'),'queue',`data-index="${index}" aria-label="Tocar ${text(item.title)}"`,s.connected&&m.queue_freshness==='fresh'&&!!item.item_id&&!busy('queue_play'))}</div>`).join('') || empty(m.queue_freshness==='unavailable'?'Nenhuma fila observada nesta reprodução.':'A fila observada não tem próximas faixas.'),fresh(m.queue_freshness),`<span class="tp-pill">${rows.length} na fila</span>`);
  }
  function catalog() {
    const m = music(), all = list(m.catalog).filter(item => String(item.name||'').toLocaleLowerCase('pt-BR').includes(ui.catalog.toLocaleLowerCase('pt-BR'))), visible = ui.all?all:all.slice(0,6);
    return section('Suas playlists',`${search('catalog',ui.catalog,'Buscar no catálogo')}<div class="tp-playlists tp-gap">${visible.map(item => `<div class="tp-playlist-wrap"><button class="tp-playlist ${item.name===m.playlist?'active':''}" data-tp-action="playlist-open" data-name="${esc(item.name)}"${disabled(s.connected&&m.catalog_available===true)}>${artwork(item.artwork_url,'',item.name)}<strong>${text(item.name)}</strong><small>${text(item.count)} faixas${item.name===m.playlist?' · ativa':''}</small></button><button class="tp-playlist-play" data-tp-action="playlist-play" data-name="${esc(item.name)}" aria-label="Tocar ${esc(item.name)}"${disabled(s.connected&&m.catalog_play_available===true&&!busy('playlist_play'))}>${ico('play')}</button></div>`).join('')||empty(m.catalog_available?'Nenhuma playlist salva.':'Catálogo indisponível. Aguardando a Laylay.')}</div>${all.length>6?`<div class="tp-gap-sm">${button(ui.all?'Mostrar menos':'Ver todas as playlists','catalog-all')}</div>`:''}`,'Biblioteca da Laylay',`<span class="tp-pill">${list(m.catalog).length} playlists</span>`);
  }
  function lyrics() {
    const lyric = obj(music().lyrics), lines = list(lyric.lines), position = number(music().position_seconds)??0;
    let current = -1; lines.forEach((line,index)=>{if(Number(line.time_seconds)<=position)current=index;});
    const visible = ui.lyrics?lines:lines.slice(Math.max(0,current-1),Math.max(3,current+3));
    const messages = {idle:'Aguardando uma faixa observada.',loading:'Procurando a letra na LRCLIB…',instrumental:'Faixa identificada como instrumental.',not_found:'A LRCLIB não encontrou uma letra compatível.',rate_limited:'Aguardando o limite de consulta da LRCLIB.',error:'Não foi possível consultar a letra agora.'};
    const body = lyric.status==='available' ? `<div class="tp-lyrics ${ui.lyrics?'expanded':''}" tabindex="0" aria-label="Letra da faixa">${lines.length?visible.map(line=>`<p class="${line===lines[current]?'active':''}">${text(line.text)}</p>`).join(''):`<p style="white-space:pre-line">${text(lyric.plain_text)}</p>`}</div>${button(ui.lyrics?'Recolher letra':'Ver letra completa','lyrics')}` : `<p>${esc(messages[lyric.status]||'Letra indisponível.')}</p>`;
    return section('Letra',body,lyric.status==='available'?`LRCLIB · ${lyric.synced?'sincronizada':'sem sincronização'}`:'Fonte: LRCLIB');
  }
  function audioOutput() {
    const audio = obj(music().audio_output);
    return section('Saída de áudio',`${kv('Dispositivo',text(audio.name))}${kv('Origem',text(audio.source))}<label class="tp-formfield">Trocar dispositivo<select data-field="tp-output" data-tp-change="audio"${disabled(s.connected&&audio.switch_available===true&&!busy('audio_output_select'))}><option value="">Escolher saída</option>${list(audio.devices).map(device=>`<option value="${esc(device.ref)}"${device.ref===audio.selected_ref?' selected':''}>${text(device.name)}</option>`).join('')}</select></label>`,audio.available?'Saída observada pelo sistema':'Nenhuma saída publicada');
  }
  function routines() {
    const routine = obj(obj(s.dashboard).routines);
    return list(routine.items).map((item,index)=>`<div class="tp-list-line"><div class="tp-list-copy"><strong>${text(item.name)}</strong><small>${text(item.time)} · ${text(item.date||list(item.days).join(', '))}</small></div>${button('Cancelar','routine-cancel',`data-index="${index}"`,s.connected&&item.can_disable===true&&!busy('routine_cancel'))}</div>`).join('')||empty('Nenhuma rotina publicada agora.');
  }
  function playlistDetail() {
    const d = obj(ui.detail), m = music();
    const rows=list(d.items).map((item,index)=>{
      const current=m.video_id===item.video_id&&m.freshness==='fresh';
      const attrs=`data-video="${esc(item.video_id)}" aria-label="Tocar ${text(item.title)}"`;
      return `<div class="tp-tracktable ${current?'current':''}" data-render-key="track:${esc(ui.playlist)}:${esc(item.video_id)}"><small>${index+1}</small>${button(ico('play'),'track-play',attrs,s.connected&&!!d.revision&&!busy('playlist'),'tp-track-play')}${artwork(item.artwork_url,'small',item.title)}<button class="tp-track-copy" data-tp-action="track-play" data-video="${esc(item.video_id)}"${disabled(s.connected&&!!d.revision&&!busy('playlist'))}><strong>${text(item.title)}</strong><small>${text(item.channel)}${current?' · faixa observada':''}</small></button><span class="tp-date">${text(item.added_at)}</span><small>${duration(item.duration_seconds)}</small><button class="icon-btn" data-tp-action="track-menu" data-video="${esc(item.video_id)}" aria-label="Opções de ${text(item.title)}"${disabled(s.connected&&!!d.revision&&!busy('playlist'))}>···</button></div>`;
    }).join('');
    return `${button(ico('prev')+' Voltar à música','playlist-back')}
      <div class="tp-detail-top">${artwork(d.artwork_url,'large',ui.playlist)}<div><span class="tp-soft-label">PLAYLIST</span><h2>${esc(ui.playlist)}</h2><p>${d.total===undefined?'—':text(d.total)} faixas · ${duration(d.duration_seconds)}</p><div class="tp-actions tp-gap-sm">${button(ico('play')+' Tocar','playlist-play',`data-name="${esc(ui.playlist)}"`,s.connected&&m.catalog_play_available===true&&!busy('playlist_play'),'active')}${button('⇄ Aleatório','playlist-shuffle',`data-name="${esc(ui.playlist)}"`,s.connected&&m.catalog_play_available===true&&!busy('playlist_shuffle'))}${button('Trocar capa','playlist-cover','',s.connected&&!!d.revision&&!busy('playlist'))}${button('Restaurar capa','playlist-cover-restore','',s.connected&&!!d.revision&&!busy('playlist'))}</div></div></div>
      ${ui.detailMessage?note(ui.detailMessage):''}
      <section class="tp-section"><div class="tp-head">${search('trackQuery',ui.trackQuery,'Buscar faixa ou canal')}${button('Buscar','playlist-search','',s.connected&&!busy('playlist'))}${button('+ Adicionar URL','playlist-add','',s.connected&&!busy('playlist'))}</div>
      <div class="tp-tablebox"><div class="tp-thead"><span>#</span><span>Play</span><span class="tp-art-heading"></span><span>Faixa / canal</span><span class="tp-date">Adicionada</span><span>Tempo</span><span></span></div>${rows||empty(busy('playlist')?'Carregando…':'Nenhuma faixa encontrada.')}</div>${d.has_more?button('Carregar mais faixas','playlist-more','style="margin-top:14px"',!busy('playlist')):''}</section>
      <div class="tp-bottom-player" data-render-key="playlist-player">${artwork(m.artwork_url,'small',m.title)}<div class="tp-track-copy"><strong>${text(m.title)}</strong><small>${text(m.channel)}</small></div>${playbackMeter()}<span class="tp-times">${duration(m.position_seconds)} / ${duration(m.duration_seconds)}</span>${button(ico(m.state==='playing'?'pause':'play'),'media-toggle','aria-label="Pausar ou continuar"',s.connected&&m.controls_available===true&&!busy('media_toggle'))}</div>`;
  }
  p.views.music = () => {
    const context = obj(music().context_music);
    return wrap('SUA TRILHA, COM TODOS OS DETALHES','Música','Player, biblioteca, contexto e controles no mesmo lugar.',ui.playlist?playlistDetail():`<div class="tp-music-content">${player()}${queue()}${catalog()}${section('Contexto musical',`<p>${text(context.summary)}</p>${context.recommendation?`<p class="tp-gap-sm">${text(context.recommendation)}</p>`:''}<div class="tp-chips">${list(context.basis).slice(0,3).map(item=>`<span>${text(({horario_local:'Horário local',playlist_ativa:'Playlist escolhida',preferencia_confirmada:'Preferência confirmada',jogo_ativo:'Jogo observado'})[item]||item)}</span>`).join('')}</div>`,fresh(context.freshness))}${audioOutput()}${lyrics()}</div>`);
  };
  const metrics = [
    ['cpu_percent','CPU','#eb9b8e'],['gpu_percent','GPU','#78bea2'],
    ['ram_percent','RAM','#d5aa76'],['vram_percent','VRAM','#b395e8'],
    ['network_percent','Rede','#66bbd0'],['disk_percent','Disco','#83b3ea'],
  ];
  function metricValue(key) { return number(obj(obj(obj(s.dashboard).system)[key]).value); }
  function sampleDashboard() {
    const system = obj(obj(s.dashboard).system);
    for (const [key] of metrics) {
      const m = obj(system[key]), time = number(m.observed_at);
      const signature = `${time}:${m.value}`;
      if (!time || m.freshness!=='fresh' || number(m.value)===null || ui.lastSamples[key]===signature) continue;
      ui.lastSamples[key]=signature; ui.history[key]=[...list(ui.history[key]),m.value].slice(-24);
    }
  }
  function chart([key,name,color]) {
    const m = obj(obj(obj(s.dashboard).system)[key]), data = list(ui.history[key]), start = 24-data.length, width = 240, height=65, unit=10;
    let graph = '';
    for(let index=0;index<24;index++)graph+=`<line x1="${index*unit+5}" y1="0" x2="${index*unit+5}" y2="65" stroke="#ffffff04"/>`;
    const points=data.map((value,index)=>`${(start+index)*unit+5},${height-value/100*height}`).join(' ');
    if (['ram_percent','vram_percent'].includes(key)) graph+=data.map((value,index)=>`<rect x="${(start+index)*unit+2}" y="${height-value/100*height}" width="6" height="${value/100*height}" rx="1.5" fill="${color}" opacity=".7"/>`).join('');
    else if(data.length) graph+=`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.7" stroke-linejoin="round"/>${data.length===1?`<circle cx="235" cy="${height-data[0]/100*height}" r="2" fill="${color}"/>`:''}`;
    const network = key==='network_percent'?`↓ ${text(metricValue('download_mbps'))} Mbps · ↑ ${text(metricValue('upload_mbps'))} Mbps`:fresh(m.freshness);
    return `<article class="tp-chart"><div class="tp-chart-label"><strong style="color:${color}">${name}</strong><b>${percent(m.value)}</b></div><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${name}: ${data.length} de 24 posições, agora à direita">${graph}</svg><div class="tp-chart-foot"><span>24 posições · ${data.length} leituras</span><span>agora →</span></div><p class="tp-summary-text tp-gap-sm">${network}</p></article>`;
  }
  function modelSection() {
    const llm=obj(obj(obj(s.dashboard).health).llm);
    return section('Modelo local',`${kv('Status',text(llm.label))}${kv('Provedor',text(llm.provider_label||llm.provider))}${kv('Modelo',text(llm.model))}${kv('Estado',text(llm.state))}${kv('Frescor',fresh(llm.freshness))}<div class="tp-unpublished">${['Tokens/s','Latência média','Contexto atual','Fila de requisições'].map(label=>`<div><small>${label}</small><b>—</b><span>Não publicado pelo terminal</span></div>`).join('')}</div>`,'Disponibilidade e inferência permanecem separadas');
  }
  function audioSection() {
    const mic=obj(obj(obj(s.dashboard).health).microphone), audio=obj(music().audio_output);
    return section('Áudio & entrada',`${kv('Microfone',text(mic.label))}${kv('Saída',text(audio.name))}${kv('Modo',s.interactionMode==='voice'?'Voz':'Chat')}${kv('Captura',s.voiceAvailable?(s.interactionMode==='voice'?'Modo voz ativo':'Disponível · modo Chat'):'Indisponível')}${kv('Frescor',fresh(mic.freshness))}`);
  }
  function processes() {
    const health=obj(obj(s.dashboard).health);
    return section('Processos & módulos',`<div class="tp-process head"><span>Módulo</span><span>Status</span><span>CPU</span><span>RAM</span><span>VRAM</span></div>${[['llm','Modelo local'],['memory','Memória'],['microphone','Microfone']].map(([key,label])=>`<div class="tp-process"><span>${label}</span><span>${text(obj(health[key]).label)}</span><span>—</span><span>—</span><span>—</span></div>`).join('')}<div class="tp-process"><span>Telemetria</span><span>${text(obj(s.dashboard).status)}</span><span>—</span><span>—</span><span>—</span></div>${note('Consumo individual por módulo não publicado.')}`);
  }
  function quickActions() {
    const labels={open_vscode:'Abrir VS Code',organize_desktop:'Organizar desktop',briefing:'Briefing'};
    return list(obj(s.dashboard).quick_actions).filter(a=>labels[a.id]).map(a=>button(labels[a.id],'quick',`data-id="${esc(a.id)}" title="${text(a.reason)}"`,s.connected&&a.state==='available'&&!busy(a.id))).join('')||empty('Ações rápidas indisponíveis.');
  }
  p.views.system = () => {
    const d=obj(s.dashboard), system=obj(d.system), info=obj(system.info), health=obj(d.health);
    const hardware=[['os','Sistema operacional'],['cpu','Processador'],['gpu','GPU'],['ram','RAM instalada'],['vram','VRAM instalada'],['disk','Disco principal']].map(([key,label])=>kv(label,`${text(obj(info[key]).value)}${obj(info[key]).detail?`<small style="display:block">${text(obj(info[key]).detail)}</small>`:''}`)).join('');
    const events=list(s.events).slice(-5).reverse();
    return wrap('UMA VISÃO CLARA DO QUE ACONTECE','Sistema','Hardware, modelo, entrada e saúde dos módulos, com os limites de cada leitura.',`<div class="tp-main-grid tp-system-layout"><main>${section('Visão geral do hardware',`<div class="tp-hardware">${hardware}${kv('Uptime',metricValue('uptime_seconds')===null?'—':`${Math.floor(metricValue('uptime_seconds')/3600)} h ${Math.floor(metricValue('uptime_seconds')%3600/60)} min`)}${kv('Temperatura média',metricValue('temperature_c')===null?'—':`${text(metricValue('temperature_c'))} °C`)}</div>`)}<div class="tp-head"><div><h3>Histórico de uso</h3><p>Últimas 24 leituras publicadas, em posições fixas.</p></div></div><div class="tp-chart-grid">${metrics.map(chart).join('')}</div><div class="tp-notice">A ausência de leitura fica vazia. Valores anteriores não confirmam o estado atual.</div><div class="tp-gap">${modelSection()}${audioSection()}${processes()}</div>${section('Ações rápidas',`<div class="tp-actions">${quickActions()}</div>`)}${section('Eventos recentes',events.map(e=>`<div class="tp-event"><time>${stamp(e.timestamp)}</time><span>${text(e.title||e.message||e.detail)}</span></div>`).join('')||empty('Nenhum evento publicado.'))}${section('Alertas',`<div class="tp-notice">${d.status==='ok'?'As informações disponíveis foram publicadas pelo runtime.':'Telemetria parcial ou indisponível. Confira o frescor de cada leitura.'}</div>`)}</main><aside class="tp-aside">${section('Laylay',`${kv('Estado geral',s.connected?text(s.activityLabel):'Desconectada')}${kv('Modelo',text(obj(health.llm).label))}${kv('Memória',text(obj(health.memory).label))}${kv('Voz',text(obj(health.microphone).label))}${kv('Interação',s.interactionMode==='voice'?'Voz':'Chat')}${kv('Pulso',stamp(d.generated_at))}`)}${section('Armazenamento',`<div class="tp-stat-list">${meter('Disco',metricValue('disk_percent'),'#83b3ea')}${meter('RAM',metricValue('ram_percent'),'#d5aa76')}${meter('VRAM',metricValue('vram_percent'),'#b395e8')}</div>`)}${section('Telemetria',`${kv('Estado',text(d.status))}${kv('Última publicação',stamp(d.generated_at))}${note('O histórico avança apenas quando uma nova leitura é publicada.')}`)}</aside></div>`);
  };
  function syncSettings() {
    if(ui.settingsDirty)return;
    const settings=obj(s.settings); ui.provider=String(settings.provider||''); ui.models={...obj(settings.models_by_provider)};
    ui.legacyMascot=settings.mascot_enabled===true;
    if(ui.provider&&settings.model)ui.models[ui.provider]=settings.model;
  }
  function setting(label,copy,control) {return `<div class="tp-setting"><div><h4>${esc(label)}</h4><p>${esc(copy)}</p></div>${control}</div>`;}
  function preference(name,label,value) {return `<button class="toggle" role="switch" aria-label="${esc(label)}" aria-checked="${value===true}" data-tp-action="preference" data-name="${name}" data-value="${value===true?'false':'true'}"></button>`;}
  p.views.settings=()=>{
    syncSettings(); const settings=obj(s.settings), provider=ui.provider, preferences=obj(s.preferences);
    const endpoint=provider===settings.provider?settings.base_url:({ollama:'http://localhost:11434/v1',portatil:'Gerenciada pelo runtime portátil',openrouter:'https://openrouter.ai/api/v1'})[provider];
    return wrap('OS MESMOS CONTROLES, UM NOVO ACABAMENTO','Configurações','Modelo, voz, perfil e preferências da sua Laylay.',`${section('Modelo de linguagem',`<p>A configuração passa a valer após o reinício confirmado do aplicativo.</p><div class="tp-providers">${[['ollama','Local','Ollama'],['portatil','Portátil','llama.cpp'],['openrouter','OpenRouter','API protegida']].map(([id,label,detail])=>`<button class="tp-provider ${provider===id?'active':''}" data-tp-action="provider" data-id="${id}" aria-pressed="${provider===id}"${disabled(s.connected&&!busy('settings'))}><span class="tp-radio"></span><strong>${label}</strong><small>${detail}</small></button>`).join('')}</div><label class="tp-formfield">Modelo<input data-tp-input="model" data-field="tp-model-${esc(provider)}" value="${esc(ui.models[provider]||'')}" placeholder="Nome local ou ID do modelo"${disabled(s.connected&&!!provider&&!busy('settings'))}></label><div class="tp-formfield"><label>Endpoint · somente leitura</label><div class="tp-endpoint tp-mono">${text(endpoint)}</div></div>${provider==='openrouter'?`<hr class="tp-divider"><div class="tp-row tp-between"><h4>Credencial OpenRouter</h4><span class="tp-pill">${settings.api_key_configured?'Configurada · protegida':'Não configurada'}</span></div><label class="tp-formfield">Alteração da credencial<select data-tp-change="credential" data-field="tp-credential">${[['preserve','Manter credencial atual'],['replace','Substituir credencial'],['remove','Remover credencial']].map(([id,label])=>`<option value="${id}"${ui.credentialAction===id?' selected':''}>${label}</option>`).join('')}</select></label>${ui.credentialAction==='replace'?'<label class="tp-formfield">Nova chave<input type="password" id="tp-api-key" autocomplete="new-password" placeholder="A chave não será exibida novamente" spellcheck="false"></label>':''}`:''}<label class="tp-formfield"><span><input type="checkbox" data-tp-change="legacy-mascot"${ui.legacyMascot?' checked':''}${disabled(s.connected&&!busy('settings'))}> Mascote externo legado</span><small>Preferência separada do rosto integrado desta interface.</small></label>${ui.settingsMessage?note(ui.settingsMessage):''}${settings.restart_required?note('Há configuração salva aguardando reinício.'):''}<div class="tp-actions tp-gap">${button(busy('settings')?'Aguardando confirmação…':ico('check')+' Salvar configuração','settings-save','',s.connected&&!!provider&&!busy('settings'),'active')}${button('Reiniciar Laylay','restart','',s.connected&&!busy('restart'))}</div>`,'Provedor, modelo e credencial')}${section('Voz',`${kv('Ouvido / captura',s.voiceAvailable?'Disponível':'Indisponível')}${kv('Modo confirmado',s.interactionMode==='voice'?'Voz':'Chat')}${setting('Modo de interação','O modo só muda quando o ouvido confirma a solicitação.',`<div class="tp-actions">${button('Chat','voice','data-mode="chat"',s.connected&&!busy('voice'),s.interactionMode==='chat'?'active':'')}${button('Voz','voice','data-mode="voice"',s.connected&&s.voiceAvailable&&!busy('voice'),s.interactionMode==='voice'?'active':'')}</div>`)}`)}${section('Perfil',`<div class="tp-row"><span class="tp-profile-circle">${s.userAvatar?`<img src="${esc(s.userAvatar)}" alt="Seu avatar" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`:'○'}</span><div style="flex:1"><h4>Seu avatar</h4><p>Usado ao lado das suas mensagens.</p></div>${button('Trocar foto','avatar')}</div>`)}${section('Interface',`${setting('Manter sidebar expandida','Navegação lateral do seu espaço.',preference('sidebar','Manter sidebar expandida',preferences.sidebar))}${setting('Mostrar mascote','Rosto integrado nos três formatos.',preference('mascot','Mostrar mascote',preferences.mascot))}${setting('Cor de destaque','Violeta ou ciano.',`<div class="swatches">${['violet','cyan'].map(color=>`<button class="swatch ${preferences.accent===color?'selected':''}" style="--swatch:${color==='violet'?'#ad92ff':'#7fd2e4'}" data-tp-action="accent" data-value="${color}" aria-label="Usar ${color==='violet'?'violeta':'ciano'}" aria-pressed="${preferences.accent===color}"></button>`).join('')}</div>`)}${setting('Reduzir movimento','Desativa a flutuação, o olhar e as piscadas animadas.',preference('reduzir_movimento','Reduzir movimento',preferences.reduced))}${setting('Posição da ilha','Uma companhia discreta no alto da tela.','<span class="tp-soft-label">Topo · centro</span>')}`)}`);
  };
  p.views.lamp=()=>{
    const d=obj(s.dashboard), iot=obj(d.iot), devices=list(iot.devices), context=obj(d.context), confirmed=devices.filter(item=>item.state_confirmed===true).length;
    return wrap('SEU ESPAÇO, EM SINTONIA','Automação','Dispositivos, rotinas e estados observados.',`<div class="tp-counts"><div class="tp-count"><b>${devices.length}</b><span>Dispositivos publicados</span></div><div class="tp-count"><b>${confirmed}</b><span>Estados confirmados</span></div><div class="tp-count"><b>${list(obj(d.routines).items).length}</b><span>Rotinas ativas</span></div></div><div class="tp-main-grid"><main>${section('Casa agora',devices.map((device,index)=>`<article class="tp-device"><div class="tp-icon-box">${ico('lamp')}</div><div class="tp-list-copy"><h4>${text(device.display_name)}</h4><p>${text(device.room)} · ${text(device.type)}</p><small>${device.state_confirmed?text(({on:'Ligado · confirmado',off:'Desligado · confirmado'})[device.state]):text(device.state==='offline'?'Offline':'Estado não confirmado')}</small>${number(device.brightness_percent)!==null?`<label class="tp-formfield">Brilho ${percent(device.brightness_percent)}<input type="range" min="1" max="100" value="${device.brightness_percent}" data-tp-change="brightness" data-index="${index}" aria-label="Brilho de ${text(device.display_name)}"${disabled(s.connected&&iot.controls_available===true&&list(device.capabilities).includes('ajustar_brilho')&&!busy('iot_brightness'))}></label>`:''}</div><div class="tp-stack">${button('Atualizar','iot-status',`data-index="${index}"`,s.connected&&iot.controls_available===true&&!busy('iot_status'))}${button('Ligar','iot-on',`data-index="${index}"`,s.connected&&iot.controls_available===true&&list(device.capabilities).includes('ligar')&&!busy('iot_power'))}${button('Desligar','iot-off',`data-index="${index}"`,s.connected&&iot.controls_available===true&&list(device.capabilities).includes('desligar')&&!busy('iot_power'))}</div></article>`).join('')||empty('Nenhum dispositivo publicado.'),`${fresh(iot.freshness)} · ${show(iot.mode)}`)}${section('Rotinas & agenda',routines())}${section('Pedidos em andamento',list(s.events).filter(e=>e.state==='awaiting_confirmation'||e.state==='partial'||e.state==='failed').slice(-5).map(e=>`<div class="tp-list-line"><div><strong>${text(e.summary||e.title)}</strong><small>${text(e.state)}</small></div></div>`).join('')||empty('Nenhuma pendência publicada nesta projeção.'))}</main><aside>${section('Contexto de jogo',`${kv('Estado',context.freshness==='unavailable'?'Indisponível':context.game_active?'Jogo observado':'Nenhum jogo observado')}${kv('Jogo',text(context.game_name))}${note('O contexto é observado pelo runtime. Esta tela não concede autorização.')}`)}${section('Estado da integração',`${kv('Provedor',iot.provider_available?'Disponível':'Indisponível')}${kv('Controles',iot.controls_available?'Disponíveis':'Somente leitura')}${kv('Observado em',stamp(iot.observed_at))}`)}</aside></div>`);
  };
  p.views.memory=()=>{
    const items=list(obj(s.dashboard).memory_recent), health=obj(obj(obj(s.dashboard).health).memory), names={preference:'Preferências',reminder:'Lembretes',task:'Ações confirmadas'};
    const selected=items.filter(item=>(!ui.memoryCategory||item.kind===ui.memoryCategory)&&`${item.summary||''} ${item.detail||''}`.toLocaleLowerCase('pt-BR').includes(ui.memoryQuery.toLocaleLowerCase('pt-BR')));
    return wrap('O QUE CONTINUA COM A GENTE','Memória','Projeção segura de memórias recentes, com origem e confirmação.',`${section('Estado da memória',`${kv('Serviço',text(health.label))}${kv('Frescor',fresh(health.freshness))}${kv('Itens publicados',String(items.length))}`)}<div class="tp-category-counts">${[['','Todas'],...Object.entries(names)].map(([id,label])=>button(`<b>${id?items.filter(item=>item.kind===id).length:items.length}</b>${label}`,'memory-category',`data-id="${id}"`,true,ui.memoryCategory===id?'active':'')).join('')}</div>${section('Memórias recentes',`${search('memoryQuery',ui.memoryQuery,'Buscar memórias publicadas')}${selected.map(item=>`<article class="tp-memory"><h4>${text(item.summary)}</h4><p>${text(item.detail)}</p><div class="tp-memory-meta"><span class="tp-pill">${esc(names[item.kind]||'Outras')}</span><span>${text(({agenda_confirmed:'Agenda confirmada',user_confirmed:'Confirmação do usuário',executor_confirmed:'Receipt do executor'})[item.source])}</span><time>${stamp(item.timestamp)}</time></div></article>`).join('')||empty('Nenhuma memória corresponde à busca.')}`)}${note('Esta projeção contém apenas itens que o serviço de memória publicou. A contagem não representa todo o armazenamento.')}`);
  };
  p.views.streaming=()=>wrap('SEU VÍDEO, NO SEU ESPAÇO','Streaming','Player local independente da inteligência da Laylay.',`${section('Janela de transmissão',`<div class="tp-stream-screen"><div class="tp-stream-art"></div><div class="tp-stream-copy">${ico('play')}<h3>Seu player, por perto.</h3><p>Escolha uma janela no player nativo para assistir aqui com os controles completos.</p></div><span class="tp-stream-state">Fonte: seletor nativo</span></div><div class="tp-actions">${button('Abrir player','streaming-open','',true,'active')}${button('Parar / fechar player','streaming-stop')}</div>${note('A seleção de fonte, transmissão, enquadramento, janela flutuante e tela cheia ficam no player nativo. Nenhum frame é enviado à mente da Laylay.')}`)}${section('Áudio & controles',`<p>O áudio e os controles de reprodução continuam no navegador de origem. O player nativo mantém o mesmo recorte e detector de vídeo do terminal.</p>`)}${section('Ao sair desta página',`<p>A captura é encerrada ao trocar de página ou recolher a interface.</p>`)}`);
  const categories=['ALL','SYSTEM','IA','ROUTER','PRESENCE','EVENTS','AUTONOMY','ERRORS','TRACE','DEV/UI','CORPO'];
  function devRows() {
    const order={normal:0,debug:1,trace:2};
    return ui.devEvents.filter(event=>{
      const body=String(event.message||'').includes('[AUTONOMIA:CORPO]');
      return (ui.devCategory==='CORPO'?body:!body&&(ui.devCategory==='ALL'||event.category===ui.devCategory))&&(order[event.depth]??0)<=(order[ui.devLevel]??0);
    });
  }
  function devTerminal(rows) {
    const outputs=ui.devOutput.map(entry=>`<article class="tp-command-result" data-render-key="command:${esc(entry.id)}"><div class="tp-command-title"><span>laylay.dev ›</span> ${text(entry.command)} <small>${entry.source==='local'?'local':entry.ok?'receipt confirmado':'consulta sem confirmação'}</small></div><pre>${esc(list(entry.lines).join('\n'))}</pre></article>`).join('');
    return `<section class="tp-terminal"><header class="tp-terminal-title"><span><i></i> laylay.dev <small>terminal de diagnóstico</small></span><span class="tp-terminal-connection">${s.connected?'PONTE ONLINE':'OFFLINE'}</span></header>
      <div class="tp-dev-filters"><div class="tp-actions" role="group" aria-label="Categoria dos eventos">${categories.map(category=>button(category,'dev-category',`data-id="${category}" aria-pressed="${category===ui.devCategory}"`,true,category===ui.devCategory?'active':'')).join('')}</div>
      <div class="tp-dev-depth"><div class="tp-actions">${['normal','debug','trace'].map(level=>button(level.toUpperCase(),'dev-level',`data-id="${level}" aria-pressed="${level===ui.devLevel}"`,true,level===ui.devLevel?'active':'')).join('')}${button('INSANE · manutenção','none','',false)}</div><div class="tp-actions">${button(ui.devPaused?'PAUSED':'LIVE','dev-pause','',true,ui.devPaused?'':'active')}${button('Limpar visor','dev-clear')}</div></div></div>
      <div class="tp-console-columns" aria-hidden="true"><span>HORA</span><span>CATEGORIA</span><span>NÍVEL</span><span>EVENTO</span></div>
      <div class="tp-console" id="tp-console-viewport" tabindex="0" role="region" aria-label="Eventos técnicos">${rows.map(event=>`<div class="tp-console-line level-${['info','success','warning','error'].includes(event.level)?event.level:'info'}" data-render-key="dev:${esc(event.id||event.sequence)}"><time>${stamp(event.timestamp)}</time><b>${text(event.category)}</b><span class="tp-level">${text(event.level)}</span><span class="tp-console-message">${text(event.message)}</span></div>`).join('')||empty('Aguardando eventos do runtime.')}${outputs}</div>
      <form id="tp-dev-command" class="tp-prompt"><label for="tp-dev-input">laylay.dev <span>›</span></label><input id="tp-dev-input" data-tp-input="devCommand" data-field="tp-dev-command" value="${esc(ui.devCommand)}" placeholder="Digite help para ver os comandos" aria-label="Comando DevConsole" autocomplete="off" spellcheck="false"><button type="submit" class="tp-button"${disabled(!busy('dev-command'))}>${busy('dev-command')?'Aguardando…':'Executar ↵'}</button></form>
      <footer class="tp-terminal-foot"><span>${rows.length} eventos visíveis · ${ui.devEvents.length} no buffer</span><span>Consultas somente leitura · CONTROL exige autorização</span></footer></section>`;
  }
  p.views.dev=()=>{
    const body=obj(ui.devBody), rows=devRows(), health=obj(obj(s.dashboard).health);
    const modules=[['llm','Modelo'],['memory','Memória'],['microphone','Microfone']];
    return wrap('POR DENTRO, COM CLAREZA','DevConsole','Diagnósticos do runtime, no seu ritmo.',`
      <div class="tp-module-strip" aria-label="Saúde dos módulos">${modules.map(([key,label])=>`<div><i class="${['ready','online'].includes(obj(health[key]).state)?'ready':''}"></i><span>${label}</span><strong>${text(obj(health[key]).label)}</strong></div>`).join('')}</div>
      ${devTerminal(rows)}
      <details class="tp-dev-details"><summary>Corpo da Laylay <span>diagnóstico observacional</span></summary><div class="tp-body-grid">${kv('Conexão',text(body.conexao))}${kv('Corpo',text(body.nome_corpo))}${kv('Perfil',text(body.perfil))}${kv('Intenção',text(body.intencao))}${kv('Objetivo',text(body.objetivo_id))}${kv('Vigia de sensores',body.vigia_sensores_ativa===true?'Ativa':'Inativa ou não publicada')}${kv('Motor',body.motor_disponivel===true?(body.motor_em_andamento?'Em acionamento':'Sem acionamento em curso'):'Indisponível')}${kv('Último PWM',body.pwm_confirmado===true?'Confirmado':'Sem confirmação')}${kv('Parada',body.parada_confirmada===true?'Confirmada':'Sem confirmação')}${kv('Resultado',text(body.resultado))}${kv('Sensor frontal',text(body.sensor_frente))}${kv('Borda',text(body.sensor_borda))}${kv('MPU / inclinação',text(body.imu_estado||body.imu_inclinacao))}${kv('Diagnóstico',text(body.erro))}${kv('Deslocamento','Não medido')}</div>${note('Intenção, autorização, PWM e movimento permanecem evidências distintas.')}</details>
      <details class="tp-dev-details"><summary>Ferramentas de manutenção <span>indisponíveis</span></summary><div class="tp-actions tp-gap">${button('Maintenance DataViz','none','',false)}${button('Remote tools','none','',false)}${button('Debugger','none','',false)}</div></details>`);
  };
  function trackRequest(operation, video) {return playlist(operation,{video_id:video,revision:obj(ui.detail).revision});}
  function trackMenu(video) {
    const track=list(obj(ui.detail).items).find(item=>item.video_id===video); if(!track)return;
    dialog(track.title||'Faixa',`<div class="tp-stack">${[['play_track','Tocar agora'],['copy_track_many','Adicionar a playlists'],['move_track_many','Mover para playlists'],['remove_track','Remover desta playlist']].map(([operation,label])=>`<label class="tp-row"><input type="radio" name="operation" value="${operation}" required> ${label}</label>`).join('')}</div>`,'Continuar',values=>{
      const operation=values.get('operation');
      if(operation==='remove_track')dialog('Remover faixa?',`<p>${esc(track.title||'Faixa')} será removida de ${esc(ui.playlist)}.</p>`,'Remover',()=>trackRequest(operation,video),true);
      else if(operation==='copy_track_many'||operation==='move_track_many') {
        const targets=list(music().catalog).filter(item=>String(item.name).toLocaleLowerCase('pt-BR')!==ui.playlist.toLocaleLowerCase('pt-BR'));
        dialog(operation==='move_track_many'?'Mover para playlists':'Adicionar a playlists',`${targets.length?targets.map(item=>`<label class="tp-row" style="padding:8px 0"><input type="checkbox" name="destinations" value="${esc(item.name)}"> ${text(item.name)} <small>${text(item.count)} faixas</small></label>`).join(''):empty('Não há outra playlist publicada.')}${note('Cada destino conserva sua própria confirmação. Falhas parciais serão mostradas.')}`,'Confirmar',values=>{const destinations=values.getAll('destinations');if(destinations.length)playlist(operation,{video_id:video,revision:obj(ui.detail).revision,destinations});else p.toast('Selecione pelo menos uma playlist.');});
      } else trackRequest(operation,video);
    });
  }
  function saveSettings() {
    const key=document.getElementById('tp-api-key');
    const data={provider:ui.provider,model:String(ui.models[ui.provider]||'').trim(),api_key_action:ui.provider==='openrouter'?ui.credentialAction:'preserve',mascot_enabled:ui.legacyMascot};
    const legacy=document.querySelector('[data-tp-change="legacy-mascot"]'); if(legacy)data.mascot_enabled=legacy.checked;
    if(data.api_key_action==='replace')data.api_key=key?.value||'';
    if(!data.model){p.toast('Informe o modelo.');return;}
    ui.settingsMessage='Aguardando confirmação do serviço de configuração…';
    request('configuracao_salvar',data,'settings');
    if(key)key.value='';
  }
  function runDev(command) {
    const value=String(command||'').trim(); if(!value)return;
    if(value==='clear'){ui.devEvents=[];ui.devOutput=[];invalidate();return;}
    if(value==='pause'||value==='live'){ui.devPaused=value==='pause';invalidate();return;}
    if(value==='help'||value==='events'){
      ui.devOutput=[...ui.devOutput,{id:`local:${Date.now()}`,command:value,source:'local',ok:true,lines:value==='events'?[`${ui.devEvents.length} eventos observados no buffer local.`]:[
        'Locais: help, events, pause, live, clear',
        'Consultas: status, perf, errors, trace last, inspect context, inspect pending',
        'Testes: tests list, tests status, tests run <suite_id>, tests cancel',
        'CONTROL pede autorização antes de iniciar ou cancelar uma suíte.',
      ]}].slice(-12);invalidate();return;
    }
    if(/^tests (?:run |cancel$)/.test(value))dialog('Autorizar comando CONTROL?',`<p class="tp-mono">${esc(value)}</p><p>Este comando pode iniciar ou cancelar uma suíte real. O resultado será publicado pelo executor.</p>`,'Autorizar',()=>request('dev_controle',{command:value},'dev-command'));
    else request(value.startsWith('tests ')?'dev_controle':'dev_consulta',{command:value},'dev-command');
  }
  document.addEventListener('click',event=>{
    const target=event.target.closest('[data-tp-action]'); if(!target||target.disabled)return;
    const a=target.dataset.tpAction,m=music(),name=target.dataset.name;
    if(a==='media-previous')action('media_previous','volta para a música anterior');
    else if(a==='media-next')action('media_next','vai para a próxima música');
    else if(a==='media-toggle')action('media_toggle',m.state==='playing'?'pausa a música':'continua a música',{command:m.state==='playing'?'pause':'play'});
    else if(a==='repeat')action('media_repeat','alterna a repetição da música');
    else if(a==='replay')action('media_replay','reinicia essa música');
    else if(a==='shuffle'||a==='playlist-shuffle') {const pl=name||m.playlist;if(pl)action('playlist_shuffle',`toca a playlist ${pl} em modo aleatório`,{playlist:pl});}
    else if(a==='queue'){const index=Number(target.dataset.index),item=list(m.queue)[index];if(item)action('queue_play',`toca ${item.title||'a faixa'} da fila`,{item_id:item.item_id,queue_index:index,queue_source:m.queue_source});}
    else if(a==='playlist-play'&&name)action('playlist_play',`toca a playlist ${name}`,{playlist:name});
    else if(a==='playlist-open'){ui.playlist=name||'';ui.trackQuery='';detail();invalidate();}
    else if(a==='playlist-back'){ui.playlist='';ui.detail=null;invalidate();}
    else if(a==='catalog-all'){ui.all=!ui.all;invalidate();}
    else if(a==='lyrics'){ui.lyrics=!ui.lyrics;invalidate();}
    else if(a==='playlist-search')detail();
    else if(a==='playlist-more')detail(list(obj(ui.detail).items).length);
    else if(a==='track-play')trackRequest('play_track',target.dataset.video);
    else if(a==='track-menu')trackMenu(target.dataset.video);
    else if(a==='playlist-cover')playlist('set_artwork',{revision:obj(ui.detail).revision});
    else if(a==='playlist-cover-restore')dialog('Restaurar capa automática?','<p>A capa voltará a ser escolhida pelo catálogo.</p>','Restaurar',()=>playlist('restore_artwork',{revision:obj(ui.detail).revision}));
    else if(a==='playlist-add')dialog('Adicionar faixa','<label class="tp-formfield">URL do vídeo no YouTube<input type="url" name="url" required autocomplete="off" placeholder="https://www.youtube.com/watch?v=…"></label>','Adicionar',values=>playlist('add_url',{url:String(values.get('url')||'').trim()}));
    else if(a==='provider'){ui.provider=target.dataset.id;ui.settingsDirty=true;invalidate();}
    else if(a==='settings-save')saveSettings();
    else if(a==='restart')dialog('Reiniciar a Laylay?','<p>O aplicativo será reiniciado para aplicar as configurações salvas.</p>','Reiniciar',()=>request('reiniciar',{},'restart'));
    else if(a==='voice')request('voz',{mode:target.dataset.mode},'voice');
    else if(a==='avatar')p.request('preferencia',{name:'avatar',value:'selecionar'});
    else if(a==='preference')p.request('preferencia',{name:target.dataset.name,value:target.dataset.value==='true'});
    else if(a==='accent')p.request('preferencia',{name:'cor',value:target.dataset.value});
    else if(a==='routine-cancel'){const r=list(obj(obj(s.dashboard).routines).items)[Number(target.dataset.index)];if(r)dialog('Cancelar rotina?',`<p>${esc(r.name)}</p>`,'Cancelar rotina',()=>action('routine_cancel',`cancela a rotina ${r.name}`,{name:r.name}),true);}
    else if(a.startsWith('iot-')){const d=list(obj(obj(s.dashboard).iot).devices)[Number(target.dataset.index)];if(d){if(a==='iot-status')action('iot_status',`atualiza o estado de ${d.display_name}`,{device:d.name});else {const state=a==='iot-on'?'on':'off';action('iot_power',`${state==='on'?'liga':'desliga'} ${d.display_name}`,{device:d.name,state});}}}
    else if(a==='quick'){const id=target.dataset.id,requests={open_vscode:'abre o Visual Studio Code',organize_desktop:'organiza o desktop automaticamente',briefing:'me passa o briefing de hoje'};if(requests[id])action(id,requests[id]);}
    else if(a==='memory-category'){ui.memoryCategory=target.dataset.id;invalidate();}
    else if(a==='streaming-open')p.request('streaming',{operation:'open'});
    else if(a==='streaming-stop')p.request('streaming',{operation:'stop'});
    else if(a==='dev-category'){ui.devCategory=target.dataset.id;invalidate();}
    else if(a==='dev-level'){ui.devLevel=target.dataset.id;invalidate();}
    else if(a==='dev-pause'){ui.devPaused=!ui.devPaused;invalidate();}
    else if(a==='dev-clear'){ui.devEvents=[];ui.devOutput=[];invalidate();}
  });
  document.addEventListener('input',event=>{
    const field=event.target.dataset.tpInput;
    if(field==='model'){ui.models[ui.provider]=event.target.value;ui.settingsDirty=true;}
    else if(['catalog','trackQuery','memoryQuery','devCommand'].includes(field)){ui[field]=event.target.value;if(field==='catalog'||field==='memoryQuery')invalidate();}
    if(event.target.dataset.tpChange==='volume'){const output=document.querySelector('[data-tp-volume]');if(output)output.textContent=`${event.target.value}% · solicitado ao soltar`;}
  });
  document.addEventListener('change',event=>{
    const field=event.target.dataset.tpChange,value=event.target.value;
    if(field==='credential'){ui.credentialAction=value;invalidate();}
    else if(field==='legacy-mascot'){ui.legacyMascot=event.target.checked;ui.settingsDirty=true;}
    else if(field==='volume')action('volume_set',`deixa o volume em ${value} por cento`,{level:Number(value)});
    else if(field==='audio'&&value){const device=list(obj(music().audio_output).devices).find(item=>item.ref===value);if(device)action('audio_output_select',`trocar a saída de áudio para ${device.name}`,{device_ref:device.ref});}
    else if(field==='brightness'){const d=list(obj(obj(s.dashboard).iot).devices)[Number(event.target.dataset.index)];if(d)action('iot_brightness',`ajusta o brilho de ${d.display_name} para ${value} por cento`,{device:d.name,value:Number(value)});}
  });
  document.addEventListener('submit',event=>{if(event.target.id==='tp-dev-command'){event.preventDefault();const command=ui.devCommand;ui.devCommand='';event.target.querySelector('input').value='';runDev(command);}});
  p.onEvent(event=>{
    const type=event.type;
    if(type==='music_meter'){
      const levels=list(event.levels);
      if(event.video_id===music().video_id&&levels.length===3&&levels.every(v=>number(v)!==null&&v>=0&&v<=1)&&number(event.observed_at)!==null){
        ui.musicMeter={video_id:event.video_id,levels,observed_at:event.observed_at};updateMeter();
        clearTimeout(meterExpiry);meterExpiry=setTimeout(updateMeter,2050);
      }
      return;
    }
    if(type==='dashboard_state'||type==='snapshot')sampleDashboard();
    if(type==='settings_state'&&!ui.settingsDirty)syncSettings();
    if(type==='settings_result'){ui.settingsMessage=String(event.message||(event.saved?'Configuração salva pelo serviço.':'Configuração não confirmada.'));if(event.saved){ui.settingsDirty=false;ui.credentialAction='preserve';syncSettings();}document.getElementById('tp-api-key')?.setAttribute('value','');}
    if(type==='playlist_result') {
      const r=obj(event.result), pending=ui.requests.get(event.id);
      if(event.operation==='detail'&&event.playlist===ui.playlist&&(!pending||pending.query===ui.trackQuery)) {
        if(r.ok){const previous=obj(ui.detail);ui.detail={...r,offset:0,items:r.offset>0?[...list(previous.items),...list(r.items)]:list(r.items)};ui.detailMessage='';}
        else ui.detailMessage=`Não foi possível carregar a playlist: ${show(r.status)}`;
      } else if(event.playlist===ui.playlist) {
        ui.detailMessage=r.ok?(r.source_removed===false&&String(event.operation).startsWith('move')?'Cópia confirmada; remoção da origem não confirmada.':`Operação confirmada: ${show(r.status)}`):`Operação não confirmada: ${show(r.status)}`;
      }
    }
    const finished=(type==='input_ack'&&event.accepted===false)||['playlist_result','settings_result','restart_result','mode_state','dev_query_result','dev_control_result','error'].includes(type)||(type==='action_state'&&['confirmed','partial','failed','awaiting_confirmation'].includes(event.state));
    if(finished) {
      if(event.id){ui.finished.set(event.id,{type,result:{ok:obj(event.result).ok}});if(ui.finished.size>160)ui.finished.delete(ui.finished.keys().next().value);}
      const entry=ui.requests.get(event.id);
      if(entry){ui.pending.delete(entry.key);ui.requests.delete(event.id);}
      else if(type==='settings_result')ui.pending.delete('settings');
      else if(type==='mode_state')ui.pending.delete('voice');
      else if(type==='restart_result')ui.pending.delete('restart');
      else if(type==='action_state')ui.pending.delete(event.action);
      if(entry&&type==='playlist_result'&&event.operation!=='detail'&&obj(event.result).ok&&event.playlist===ui.playlist)detail();
    }
    if(type==='snapshot') {const dev=obj(event.dev_console);if(list(dev.events).length)ui.devEvents=list(dev.events);if(dev.body)ui.devBody=obj(dev.body);}
    if(type==='dev_events') {if(!ui.devPaused){const seen=new Set(ui.devEvents.map(e=>e.id||e.sequence));ui.devEvents=[...ui.devEvents,...list(event.events).filter(e=>!seen.has(e.id||e.sequence))].slice(-160);}if(event.body)ui.devBody=obj(event.body);}
    if(type==='dev_query_result'||type==='dev_control_result'){
      const result=obj(event.result);
      ui.devOutput=[...ui.devOutput,{id:event.id,command:result.command||'Consulta DEV',lines:list(result.lines).slice(0,120),ok:result.ok===true,source:'runtime'}].slice(-12);
    }
    if(type==='conexao'&&!event.connected){ui.pending.clear();ui.requests.clear();ui.detailMessage=ui.playlist?'Conexão interrompida. Atualize a playlist após reconectar.':'';}
    if(type==='erro_interface') {ui.pending.clear();ui.settingsMessage=String(event.message||'Pedido não enviado.');}
    // O core agenda uma única pintura após aplicar o evento em todos os subscribers.
  });
})();
