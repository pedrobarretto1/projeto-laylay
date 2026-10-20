// Interface oficial: apresenta somente eventos e dados da ponte local.
const paths={home:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',chat:'<path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-10a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8Z"/><path d="M7 10h8M7 14h5"/>',music:'<path d="M9 17V5l11-2v12M9 8l11-2"/><ellipse cx="6" cy="17.5" rx="3" ry="2.5"/><ellipse cx="17" cy="15.5" rx="3" ry="2.5"/>',lamp:'<path d="M8 14h8l4-5H4l4 5ZM12 14v6M7 21h10M8 9l1-6h6l1 6"/>',memory:'<path d="M7 4h12v17H7a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3ZM7 4v17M10 8h5M10 12h5"/>',system:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4M6 11h3l2-4 3 7 2-3h2"/>',settings:'<path d="m9 3-1 3-3 1 1 3-2 2 2 2-1 3 3 1 1 3h3l1-3 3-1 1-3 3-1v-3l-3-1-1-3-3-1-1-3Z"/><circle cx="11" cy="12" r="3"/>',chevron:'<path d="m9 5 7 7-7 7"/>',arrow:'<path d="M4 12h15m-5-5 5 5-5 5"/>',expand:'<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',collapse:'<path d="M4 8h4V4M20 8h-4V4M4 16h4v4M20 16h-4v4"/>',minus:'<path d="M5 12h14"/>',close:'<path d="m6 6 12 12M6 18 18 6"/>',play:'<path d="m8 5 11 7-11 7Z"/>',pause:'<path d="M8 5h2v14H8zM14 5h2v14h-2z"/>',next:'<path d="m5 5 10 7L5 19ZM18 5v14"/>',prev:'<path d="m19 5-10 7 10 7ZM6 5v14"/>',spark:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>',send:'<path d="M12 19V5m-5 5 5-5 5 5"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',check:'<path d="m5 12 4 4L19 6"/>',shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',heart:'<path d="M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8 6l8 8 8-8a5 5 0 0 0 0-7Z"/>',island:'<rect x="3" y="8" width="18" height="8" rx="4"/><path d="M8 12h2M14 12h2"/>',panel:'<rect x="6" y="3" width="12" height="18" rx="3"/><path d="M10 7h4M10 17h4"/>',full:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 4v16"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',refresh:'<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',volume:'<path d="m11 5-6 4H2v6h3l6 4ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>',leaf:'<path d="M20 3s-12-1-15 7a7 7 0 0 0 9 9C21 16 20 3 20 3ZM5 20l10-10"/>',calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 11h18M8 15h2"/>'};
paths.streaming='<rect x="3" y="4" width="18" height="13" rx="2"/><path d="m10 8 5 3-5 3ZM8 21h8M12 17v4"/>';
paths.dev='<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 16h4"/>';
const icon=(n)=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[n]||paths.spark)+'</svg>';

(() => {
'use strict';
const state = {
  mode:'full',page:'home',connected:false,activity:'reconnecting',activityLabel:'Reconectando',
  emotion:'calma',interactionMode:'chat',voiceAvailable:false,microphoneLevel:0,messages:[],
  draft:'',dashboard:{},settings:{},conversations:{active_id:'',items:[]},events:[],
  preferences:{reduced:false,mascot:true,accent:'violet',sidebar:true},pending:{},
  actions:{},windowVisible:true
};
const pages = [['home','Início'],['chat','Conversa'],['lamp','Automação'],['music','Música'],
  ['streaming','Streaming'],['memory','Memória'],['system','Sistema'],['dev','DevConsole'],['settings','Configurações']];
const nativePages={home:'inicio',chat:'conversa',lamp:'automacao',music:'musica',streaming:'streaming',memory:'memoria',system:'sistema',dev:'desenvolvedor',settings:'configuracoes'};
const views={};
const subscribers=new Set();
const eventReplay=[];
const pendingTimers=new Map();
let bridge=null,started=false,renderQueued=false,renderFrame=0,resetFields=false,composing=false;
let confirmation=null,toastTimer=0,previousLocation='';
const escapeHTML=(v)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const object=(v)=>v&&typeof v==='object'&&!Array.isArray(v)?v:{};
const list=(v)=>Array.isArray(v)?v:[];
function avatar(size='') {
  const classes=String(size).replace(/[^a-zA-Z0-9 _-]/g,'');
  const feeling=state.activity==='listening'?'hearing':state.activity==='thinking'?'thinking':'';
  return '<div class="avatar '+classes+' '+feeling+'" aria-hidden="true"><div class="avatar-body"></div><div class="face"><i class="eye"></i><i class="eye"></i></div><i class="smile"></i><i class="cheek"></i><i class="cheek right"></i><i class="spark"></i></div>';
}
function status() {
  return '<span class="status '+(state.connected?'':'offline')+'" title="'+escapeHTML(state.connected?'Ponte conectada · '+state.emotion:'Sem conexão com a mente')+'"><i></i>'+escapeHTML(state.connected?state.activityLabel:'Reconectando')+'</span>';
}
function pageHeading(eyebrow,title,subtitle,tag='') {
  return '<header class="page-heading"><div><div class="eyebrow">'+escapeHTML(eyebrow)+'</div><h2>'+escapeHTML(title)+'</h2>'+(subtitle?'<p>'+escapeHTML(subtitle)+'</p>':'')+'</div>'+(tag?'<span class="tag">'+escapeHTML(tag)+'</span>':'')+'</header>';
}
function compose() {
  const disabled=!state.connected||state.interactionMode==='voice';
  return '<form class="composer" data-composer>'+icon('spark')+'<input id="composer-input" aria-label="Mensagem para a Laylay" autocomplete="off" placeholder="'+(state.interactionMode==='voice'?'Modo voz · use o microfone da Laylay':'O que você tem em mente?')+'" value="'+escapeHTML(state.draft)+'" '+(disabled?'disabled':'')+'><button type="button" class="mic" data-action="voice" aria-label="'+(state.interactionMode==='voice'?'Voltar ao chat':'Usar voz')+'" '+(!state.connected||(!state.voiceAvailable&&state.interactionMode!=='voice')?'disabled':'')+'>'+icon('mic')+'</button><button class="send" aria-label="Enviar mensagem" title="Enviar mensagem" '+(disabled?'disabled':'')+'>'+icon('send')+'</button></form>';
}
function safeArtwork(value) {
  const text=String(value||'');
  if(/^https:\/\/i\.ytimg\.com\/vi\/[A-Za-z0-9_-]{11}\/[A-Za-z0-9_-]+\.jpg$/.test(text))return text;
  if(/^laylay-playlist-artwork:\/\/[a-f0-9]{24}\.png$/.test(text))return text;
  if(/^assets\/[A-Za-z0-9_./-]+\.(png|jpg|jpeg|webp)$/.test(text)&&!text.includes('..'))return text;
  return '';
}
function musicCard(quick=false) {
  const music=object(state.dashboard.music);
  const playing=music.state==='playing';
  const available=state.connected&&music.controls_available===true&&music.freshness!=='unavailable';
  const pending=Object.values(state.pending).some(p=>p.action==='media_toggle'&&['sending','accepted','received','executing'].includes(p.state));
  const url=safeArtwork(music.artwork_url);
  const duration=Number(music.duration_seconds)||0,position=Number(music.position_seconds)||0;
  const width=duration>0?Math.min(100,Math.max(0,100*position/duration)):0;
  return '<div class="'+(quick?'quick-music':'music-card')+'"><div class="album empty-art">'+(url?'<img src="'+escapeHTML(url)+'" alt="Capa da faixa">':icon('music'))+'</div><div class="music-info"><h3>'+escapeHTML(music.title||'Nenhuma faixa confirmada')+'</h3><p>'+escapeHTML(music.channel||'Aguardando o player observado')+'</p>'+(quick?'':'<div class="progress"><span style="width:'+width+'%"></span></div>')+'</div><button class="music-play" data-action="music-toggle" aria-label="'+(playing?'Pausar música':'Continuar música')+'" '+(!available||pending?'disabled':'')+'>'+icon(pending?'clock':playing?'pause':'play')+'</button></div>';
}
function activeMessages() {
  const active=String(state.conversations.active_id||'');
  return state.messages.filter(m=>!m.conversation_id||m.conversation_id===active);
}
function messages() {
  const items=activeMessages();
  if(!items.length)return '<div class="chat-empty">Seu espaço para uma nova conversa.</div>';
  return items.map(m=>{
    const user=m.role==='user',failed=m.delivery==='failed';
    const delivery=user&&m.delivery?'<small class="delivery '+(failed?'failed':'')+'">'+escapeHTML({
      sending:'Enviando…',pending:'Aguardando recebimento',accepted:'Recebida pela mente · aguardando resposta',
      failed:m.error||'Envio não confirmado',responded:'Resposta recebida'
    }[m.delivery]||m.delivery)+(failed?'<button data-retry="'+escapeHTML(m.id)+'">Tentar novamente</button>':'')+'</small>':'';
    return '<article class="message '+(user?'user':'')+'" data-render-key="'+escapeHTML(JSON.stringify([m.conversation_id||'',m.role,m.id]))+'" data-message-id="'+escapeHTML(m.id)+'">'+(user?'<span class="profile" aria-hidden="true">'+(state.userAvatar?'<img src="'+escapeHTML(state.userAvatar)+'" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%">':escapeHTML(profileName().slice(0,1)||'U'))+'</span>':avatar('avatar-mini'))+'<div class="bubble"><span class="author">'+(user?'Você':'Laylay')+'</span>'+escapeHTML(m.text)+delivery+'</div></article>';
  }).join('');
}
function profileName() { return String(state.preferences.profile_name||'').trim(); }
function conversationTitle() {
  const c=list(state.conversations.items).find(c=>String(c.id)===String(state.conversations.active_id));
  return c?.title||'Vamos conversar.';
}
function home() {
  const name=profileName(),routines=object(state.dashboard.routines);
  const items=routines.freshness==='unavailable'?[]:list(routines.items).filter(x=>x&&typeof x==='object').slice(0,3);
  const agenda=items.length?items.map(item=>'<div class="timeline-item"><div class="timeline-icon">'+icon('clock')+'</div><div><div class="time">'+escapeHTML([item.date,item.time].filter(Boolean).join(' · ')||'Horário não informado')+'</div><strong>'+escapeHTML(item.name||'Compromisso')+'</strong><p>'+escapeHTML(item.active===false?'Desativado':routines.freshness==='stale'?'Dados antigos':'Agenda observada')+'</p></div></div>').join(''):'<div class="timeline-item"><div class="timeline-icon cyan">'+icon('calendar')+'</div><div><strong>Agenda sem itens disponíveis</strong><p>'+escapeHTML(state.connected?'Nenhum compromisso foi publicado.':'Aguardando a agenda da Laylay.')+'</p></div></div>';
  const memory=list(state.dashboard.memory_recent)[0];
  const day=new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'});
  return pageHeading('SEU ESPAÇO','Bom ter você por aqui.','',day)+'<div class="home-top"><section class="presence" aria-label="Presença da Laylay"><div class="presence-copy"><div class="eyebrow" style="color:#a69ab8;margin-bottom:14px">Perto, no seu ritmo</div><h1>Estou por aqui'+(name?',<br><span>'+escapeHTML(name)+'.</span>':'.')+'</h1><p>Uma conversa, uma ideia<br>ou só uma boa companhia.</p></div><div class="scene">'+avatar()+'</div><div class="presence-status">'+status()+'</div></section><section class="today"><div class="section-title"><h3>No seu dia</h3>'+icon('calendar')+'</div><p class="agenda-day">Sua agenda, no seu ritmo.</p>'+agenda+'</section></div><div class="home-bottom"><section><div class="home-section-title"><span>Sua trilha</span><button class="text-link" data-page="music">Ver biblioteca '+icon('arrow')+'</button></div>'+musicCard()+'</section><section><div class="home-section-title"><span>Vale guardar</span><button class="text-link" data-page="memory">Ver memória '+icon('arrow')+'</button></div><div class="suggestion"><div class="suggestion-title">'+icon('memory')+' '+escapeHTML(memory?.summary||'Um lugar para suas lembranças')+'</div><p>'+escapeHTML(memory?.detail||'As informações confirmadas pela Laylay aparecem aqui.')+'</p><button data-page="memory">Abrir memória '+icon('arrow')+'</button></div></section></div><div class="home-compose">'+compose()+'<p class="composer-note">Um espaço para pensar em voz baixa.</p></div>';
}
function chat() {
  const pending=Object.values(state.pending).some(p=>p.kind==='texto'&&p.conversation_id===state.conversations.active_id&&['sending','accepted'].includes(p.state));
  return '<section class="chat-view">'+pageHeading('UM ESPAÇO PARA SUAS IDEIAS',conversationTitle(),'Pode chegar com uma pergunta ou só com vontade de falar.')+'<div class="chat-history" id="chat-history" tabindex="0" role="region" aria-label="Histórico da conversa">'+messages()+'</div><div class="chat-status-line">'+(pending?'Aguardando a resposta da Laylay…':state.interactionMode==='voice'?(state.voiceAvailable?'Modo voz · microfone da Laylay':'Ouvido indisponível'):'')+'</div>'+compose()+'<p class="composer-note">'+escapeHTML(state.connected?'Conversa conectada à Laylay.':'Reconectando à Laylay.')+'</p></section>';
}
function conversationList() {
  const items=list(state.conversations.items).filter(c=>c&&String(c.id||''));
  const visible=items.filter(c=>String(c.status||'active')!=='archived');
  const archived=items.filter(c=>String(c.status||'')==='archived');
  const rows=(data)=>data.map(c=>'<div class="conversation-row '+(String(c.id)===String(state.conversations.active_id)?'active':'')+'"><button data-conversation="'+escapeHTML(c.id)+'" '+(!state.connected?'disabled':'')+' title="'+escapeHTML(c.title||'Conversa')+'">'+(c.pinned?'◇ ':'')+escapeHTML(c.title||'Nova conversa')+'</button><button class="icon-btn" data-conversation-menu="'+escapeHTML(c.id)+'" aria-label="Opções de '+escapeHTML(c.title||'conversa')+'" '+(!state.connected?'disabled':'')+'>'+icon('more')+'</button></div>').join('');
  return '<section class="conversation-area" aria-label="Suas conversas"><div class="conversation-tools"><button data-action="new-conversation" '+(!state.connected?'disabled':'')+'>+ Nova conversa</button></div><div class="conversation-list">'+(visible.length?rows(visible):'<p class="conversation-empty">Suas conversas aparecerão aqui.</p>')+(archived.length?'<details><summary class="conversation-empty">Arquivadas · '+archived.length+'</summary>'+rows(archived)+'</details>':'')+'</div></section>';
}
function voiceSwitch() {
  return '<div class="voice-mode" aria-label="Modo de interação"><button class="'+(state.interactionMode==='chat'?'active':'')+'" data-voice="chat" '+(!state.connected?'disabled':'')+'>Chat</button><button class="'+(state.interactionMode==='voice'?'active':'')+'" data-voice="voice" '+(!state.connected||!state.voiceAvailable?'disabled':'')+'>Voz</button></div>';
}
function pageLabel() {return pages.find(p=>p[0]===state.page)?.[1]||'Início';}
function full() {
  const view=views[state.page]||({home,chat}[state.page]);
  const content=typeof view==='function'?view():pageHeading('',pageLabel(),'Aguardando a página da interface.');
  const name=profileName();
  return '<section class="window" aria-label="Interface completa"><aside class="sidebar"><div class="brand"><span class="mark" aria-hidden="true"></span>laylay</div><div class="nav-group-label">Por perto</div><nav class="nav" aria-label="Páginas da Laylay">'+pages.map(p=>'<button class="'+(state.page===p[0]?'active':'')+'" data-page="'+p[0]+'" '+(state.page===p[0]?'aria-current="page"':'')+'>'+icon(p[0])+'<span>'+p[1]+'</span></button>').join('')+'</nav>'+conversationList()+'<div class="sidebar-foot"><span class="profile">'+escapeHTML(name.slice(0,1)||'U')+'</span><div><strong>'+escapeHTML(name||'Seu espaço')+'</strong><small>Laylay · interface 1.0</small></div><button class="icon-btn" data-page="settings" aria-label="Abrir configurações">'+icon('settings')+'</button></div></aside><div class="main"><div class="titlebar"><div class="breadcrumb"><span>Laylay</span>'+icon('chevron')+'<span>'+pageLabel()+'</span></div><div class="window-actions">'+voiceSwitch()+status()+'<span class="separator"></span><button class="icon-btn" data-mode="quick" aria-label="Recolher para painel rápido" title="Painel rápido">'+icon('collapse')+'</button><button class="icon-btn" data-mode="island" aria-label="Recolher para ilha" title="Recolher para ilha">'+icon('minus')+'</button></div></div><div class="page" id="page-content">'+content+'</div><footer class="main-footer"><span>'+icon('shield')+' Seu espaço, no seu tempo.</span><span class="right-footer bridge-label">'+escapeHTML(state.connected?'Ponte conectada':'Reconectando')+' <span style="color:#9f8cb4">✧</span></span></footer></div></section>';
}
function quick() {
  const name=profileName();
  return '<section class="quick-window" aria-label="Painel rápido"><header class="quick-top"><span class="quick-brand">laylay<span class="online-dot '+(state.connected?'':'offline')+'"></span></span><div class="quick-tools"><button class="icon-btn" data-mode="full" aria-label="Abrir interface completa">'+icon('expand')+'</button><button class="icon-btn" data-mode="island" aria-label="Recolher para ilha">'+icon('minus')+'</button></div></header><div class="quick-greeting">'+avatar('avatar-small')+'<div><h2>Estou por aqui'+(name?', '+escapeHTML(name):'')+'.</h2><p>'+status()+'</p></div></div><div class="quick-history" id="chat-history" tabindex="0" role="region" aria-label="Histórico da conversa">'+messages()+'</div><div class="quick-bottom">'+musicCard(true)+compose()+'<div class="simulation-bar"><span>'+escapeHTML(state.connected?'Conversa conectada':'Reconectando')+'</span>'+voiceSwitch()+'</div><button class="quick-expand" data-mode="full">Abrir meu espaço '+icon('arrow')+'</button></div></section>';
}
function island() {
  return '<div class="island-wrap"><button class="island" data-mode="quick" aria-label="Laylay '+escapeHTML(state.connected?state.activityLabel:'Reconectando')+'. Abrir painel rápido">'+avatar('avatar-mini')+'<span><strong>Laylay</strong><small>'+escapeHTML(state.connected?state.activityLabel:'Reconectando')+'</small></span><span class="online-dot '+(state.connected?'':'offline')+'"></span></button></div>';
}
function fieldKey(el,index) {return el.id?'#'+el.id:el.getAttribute('data-field')?'field:'+el.getAttribute('data-field'):el.name?'name:'+el.name:'index:'+index;}
function savePresentation() {
  const root=document.getElementById('workspace');
  const fields=Array.from(root.querySelectorAll('input,textarea,select')).map((el,index)=>({
    key:fieldKey(el,index),focused:el===document.activeElement,
    start:el.selectionStart,end:el.selectionEnd,scroll:el.scrollTop,type:el.type
  }));
  const scroll=Array.from(root.querySelectorAll('[id],.conversation-list')).filter(el=>el.scrollHeight>el.clientHeight).map(el=>({
    key:el.id||'.conversation-list',top:el.scrollTop,bottom:el.scrollHeight-el.scrollTop-el.clientHeight<50
  }));
  return {fields,scroll};
}
function restorePresentation(saved,sameLocation) {
  const root=document.getElementById('workspace');
  const fields=Array.from(root.querySelectorAll('input,textarea,select'));
  // Os controles mantêm sua identidade e o navegador já preserva seus valores
  // editados. Reaplicar todos os valores antigos impediria leituras assíncronas
  // de preencher campos ainda intocados. Recibos usam resetFields no reconciliador.
  const composer=root.querySelector('#composer-input');
  if(composer)composer.value=state.draft;
  if(sameLocation)for(const f of saved.fields.filter(f=>f.focused)) {
    const el=fields.find((el,i)=>fieldKey(el,i)===f.key);
    if(!el||el.disabled)continue;
    el.focus({preventScroll:true});
    if(typeof f.start==='number'&&['text','search','url','tel','password'].includes(el.type)) {
      try {el.setSelectionRange(f.start,f.end);}catch(_e){}
    }
    el.scrollTop=f.scroll;
  }
  if(sameLocation)for(const s of saved.scroll) {
    const el=s.key.startsWith('.')?root.querySelector(s.key):document.getElementById(s.key);
    if(el)el.scrollTop=s.key==='chat-history'&&s.bottom?el.scrollHeight:s.top;
  }
  resetFields=false;
}
// Eventos de observação projetam diferenças; não recriam os componentes vivos.
// A chave inclui papel: uma resposta pode compartilhar o ID do envio do usuário.
function renderKey(node) {
  return node.nodeType===Node.ELEMENT_NODE?(node.getAttribute('data-render-key')||node.id||''):'';
}
function sameNode(current,next) {
  return current.nodeType===next.nodeType&&current.nodeName===next.nodeName&&renderKey(current)===renderKey(next);
}
function reconcileNode(current,next) {
  // A comparação nativa evita atravessar em JavaScript históricos e listas
  // inteiros quando sua projeção continua idêntica. Recibos que resetam campos
  // precisam percorrer os controles mesmo se os atributos não mudaram.
  if(!resetFields&&current.isEqualNode(next))return;
  if(current.nodeType!==Node.ELEMENT_NODE) {
    if(current.nodeValue!==next.nodeValue)current.nodeValue=next.nodeValue;
    return;
  }
  const mascot=current.classList.contains('avatar')&&next.classList.contains('avatar');
  for(const attr of Array.from(current.attributes)) {
    if(!next.hasAttribute(attr.name)&&!(mascot&&attr.name==='style')&&!(current.tagName==='DETAILS'&&attr.name==='open'))current.removeAttribute(attr.name);
  }
  for(const attr of Array.from(next.attributes)) {
    let value=attr.value;
    if(mascot&&attr.name==='class'&&current.classList.contains('is-blinking'))value+=' is-blinking';
    if(current.getAttribute(attr.name)!==value)current.setAttribute(attr.name,value);
  }
  reconcileChildren(current,next);
  if(resetFields&&current.matches('input,textarea,select')) {
    current.value=next.value;
    if(current.matches('input[type=checkbox],input[type=radio]'))current.checked=next.checked;
  }
}
function reconcileChildren(parent,nextParent) {
  const previous=Array.from(parent.childNodes),keyed=new Map(previous.filter(renderKey).map(node=>[renderKey(node),node]));
  const retained=new Set();let cursor=parent.firstChild;
  for(const next of Array.from(nextParent.childNodes)) {
    const key=renderKey(next);
    let current=key?keyed.get(key):cursor;
    if(!current||retained.has(current)||!sameNode(current,next))current=next.cloneNode(true);
    else reconcileNode(current,next);
    if(current!==cursor)parent.insertBefore(current,cursor);
    retained.add(current);cursor=current.nextSibling;
  }
  for(const previousNode of previous)if(!retained.has(previousNode))previousNode.remove();
}
function render(options={}) {
  if(!started||composing)return;
  if(renderFrame)cancelAnimationFrame(renderFrame);
  renderFrame=0;renderQueued=false;
  if(options.resetFields)resetFields=true;
  const root=document.getElementById('workspace');
  if(!root)return;
  const saved=savePresentation(),location=state.mode+':'+state.page;
  document.body.classList.toggle('reduced',state.preferences.reduced);
  document.body.classList.toggle('cyan',state.preferences.accent==='cyan');
  document.body.classList.toggle('tp-hide-mascot',!state.preferences.mascot);
  document.body.classList.toggle('tp-sidebar-compact',!state.preferences.sidebar);
  for(const mode of ['full','quick','island'])document.body.classList.toggle('mode-'+mode,state.mode===mode);
  const template=document.createElement('template');
  template.innerHTML=state.mode==='full'?full():state.mode==='quick'?quick():island();
  if(location===previousLocation)reconcileChildren(root,template.content);
  else root.replaceChildren(template.content);
  restorePresentation(saved,location===previousLocation);
  document.title='Laylay · '+(state.mode==='quick'?'Painel rápido':state.mode==='island'?'Ilha':pageLabel());
  if(location!==previousLocation)document.querySelector('.nav [aria-current="page"]')?.scrollIntoView({block:'nearest',inline:'nearest'});
  previousLocation=location;
  avatarMotion.refresh();
}
function scheduleRender(options={}) {
  if(options.resetFields)resetFields=true;
  if(renderQueued||!started)return;
  renderQueued=true;
  renderFrame=requestAnimationFrame(()=>{renderFrame=0;renderQueued=false;render();});
}
function toast(text) {
  const el=document.getElementById('toast');if(!el)return;
  el.textContent=String(text||'');el.classList.add('show');clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),5000);
}
function request(tipo,dados={},callback) {
  if(!bridge||typeof bridge.solicitar!=='function') {
    toast('A interface ainda está conectando à ponte.');
    if(typeof callback==='function')callback('');
    return Promise.resolve('');
  }
  const operational=!['preferencia','pagina','streaming'].includes(tipo);
  if(operational&&!state.connected) {
    toast('A Laylay está desconectada. O pedido não foi enviado.');
    if(typeof callback==='function')callback('');
    return Promise.resolve('');
  }
  const safe=object(dados);
  return new Promise(resolve=>{
    try {
      bridge.solicitar(String(tipo),JSON.stringify(safe),id=>{
        const key=String(id||'');
        if(key&&tipo!=='pagina'&&tipo!=='preferencia') {
          const old=state.pending[key]||{};
          state.pending[key]={kind:tipo,state:'sending',conversation_id:String(state.conversations.active_id||''),...old};
          if(safe.action)state.pending[key].action=String(safe.action);
          if(tipo==='texto'&&!old.messageAdded) {
            const progress=state.pending[key].state;
            upsertMessage({id:key,role:'user',text:String(safe.text||''),conversation_id:state.pending[key].conversation_id,
              delivery:['accepted','responded','failed'].includes(progress)?progress:'pending',error:state.pending[key].error});
            state.pending[key].messageAdded=true;
          }
          if(tipo==='texto'&&!['responded','failed'].includes(state.pending[key].state))armPendingTimer(key);
          scheduleRender();
        }
        if(!key&&operational)toast('O pedido não pôde ser enviado à Laylay.');
        if(typeof callback==='function')callback(key);
        resolve(key);
      });
    } catch(_error) {
      toast('Não consegui enviar o pedido pela ponte.');
      if(typeof callback==='function')callback('');
      resolve('');
    }
  });
}
function goMode(mode) {
  if(!['full','quick','island'].includes(mode))return;
  state.mode=mode;
  if(bridge&&typeof bridge.apresentar==='function')bridge.apresentar(mode);
  render();
  if(mode==='quick')scrollChat();
}
function goPage(page) {
  const normalized=Object.keys(nativePages).find(key=>key===page||nativePages[key]===page);
  if(!normalized)return;
  state.page=normalized;state.mode='full';
  if(bridge&&typeof bridge.apresentar==='function')bridge.apresentar('full');
  request('pagina',{name:nativePages[normalized]});
  render();
  if(normalized==='chat')scrollChat();
}
function scrollChat(){const el=document.getElementById('chat-history');if(el)el.scrollTop=el.scrollHeight;}
function upsertMessage(message) {
  if(!message.text)return;
  const m={id:String(message.id||''),role:message.role==='user'?'user':'assistant',text:String(message.text),
    conversation_id:String(message.conversation_id||''),timestamp:message.timestamp,...message};
  const index=state.messages.findIndex(old=>old.id===m.id&&old.role===m.role&&old.conversation_id===m.conversation_id);
  if(index>=0)state.messages[index]={...state.messages[index],...m};else state.messages.push(m);
}
function historyMessages(items,cid) {
  return list(items).filter(item=>item&&typeof item==='object').map((m,i)=>({
    id:String(m.id||'history:'+cid+':'+i+':'+(m.timestamp||'')),role:m.role==='user'?'user':'assistant',
    text:String(m.content??m.text??''),timestamp:m.timestamp,conversation_id:cid,
    delivery:['sending','pending','accepted','failed','responded'].includes(m.delivery||m.status)?String(m.delivery||m.status):'',
    error:String(m.error||'')
  })).filter(m=>m.text);
}
function setConversationSnapshot(value,replace) {
  const snapshot=object(value);
  if(snapshot.available===false)return;
  const cid=String(snapshot.active_id||'');
  state.conversations={...snapshot,active_id:cid,items:list(snapshot.items)};
  if(replace&&Array.isArray(snapshot.messages)) {
    const other=state.messages.filter(m=>m.conversation_id&&m.conversation_id!==cid);
    state.messages=other.concat(historyMessages(snapshot.messages,cid));
    for(const [id,pending] of Object.entries(state.pending)) {
      if(pending.kind==='texto'&&pending.conversation_id===cid&&pending.text)upsertMessage({
        id,role:'user',text:pending.text,conversation_id:cid,delivery:pending.state==='failed'?'failed':pending.state==='accepted'?'accepted':'pending',error:pending.error
      });
    }
  }
}
function applyState(value) {
  const data=object(value);let changed=false;
  const assign=(key,value)=>{if(state[key]!==value){state[key]=value;changed=true;}};
  if(data.activity)assign('activity',String(data.activity));
  if(data.activity_label)assign('activityLabel',String(data.activity_label));
  if(data.emotion)assign('emotion',String(data.emotion));
  if(['chat','voice'].includes(data.interaction_mode))assign('interactionMode',data.interaction_mode);
  if(typeof data.voice_available==='boolean')assign('voiceAvailable',data.voice_available);
  // Mantém a leitura disponível; nenhum componente estrutural depende deste medidor.
  if(Number.isFinite(Number(data.microphone_level)))state.microphoneLevel=Math.max(0,Math.min(1,Number(data.microphone_level)));
  return changed;
}
function failPending(id,message) {
  if(!id)return;
  clearTimeout(pendingTimers.get(id));pendingTimers.delete(id);
  const pending=state.pending[id]||(state.pending[id]={});
  pending.state='failed';pending.error=message;
  for(const m of state.messages)if(m.id===id&&m.role==='user'){m.delivery='failed';m.error=message;}
}
function armPendingTimer(id) {
  clearTimeout(pendingTimers.get(id));
  const accepted=state.pending[id]?.state==='accepted';
  pendingTimers.set(id,setTimeout(()=>{
    failPending(id,accepted?'A resposta demorou além do limite. Consulte a conversa antes de tentar novamente.':'A ponte não confirmou o recebimento.');
    scheduleRender();
  },accepted?75000:3500));
}
function receiveEvent(input) {
  let msg;
  try {msg=typeof input==='string'?JSON.parse(input):input;}catch(_error){toast('A ponte retornou um evento inválido.');return;}
  if(!msg||typeof msg!=='object'||typeof msg.type!=='string')return;
  const id=String(msg.id||''),type=msg.type;
  let repaint=true;
  if(type==='snapshot')eventReplay.length=0;
  eventReplay.push(msg);if(eventReplay.length>200)eventReplay.shift();
  if(type==='apresentacao') {
    if(['full','quick','island'].includes(msg.mode))state.mode=msg.mode;
    if(typeof msg.visible==='boolean')state.windowVisible=msg.visible;
  } else if(type==='avatar_ui') {
    const image=String(msg.data_url||'');
    state.userAvatar=/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(image)?image:'';
  } else if(type==='snapshot') {
    if(msg.conversations)setConversationSnapshot(msg.conversations,false);
    const cid=String(state.conversations.active_id||'');
    state.messages=msg.conversations&&!cid?[]:historyMessages(msg.messages,cid);
    state.events=list(msg.events);applyState(msg.state);
    if(msg.dashboard&&typeof msg.dashboard==='object')state.dashboard=msg.dashboard;
    if(msg.settings&&typeof msg.settings==='object')state.settings=msg.settings;
    if(msg.dev_console)state.devConsole=msg.dev_console;
  } else if(type==='conexao') {
    state.connected=msg.connected===true;
    if(!state.connected) {
      state.activity='reconnecting';state.activityLabel='Reconectando';state.dashboard={};state.voiceAvailable=false;
      for(const [key,p] of Object.entries(state.pending))if(['sending','accepted','received','executing'].includes(p.state))failPending(key,'Conexão interrompida antes da conclusão.');
    }
  } else if(type==='preferencias_ui') {
    const pref=object(msg.preferences||msg);
    for(const key of ['reduced','mascot','sidebar'])if(typeof pref[key]==='boolean')state.preferences[key]=pref[key];
    if(['violet','cyan'].includes(pref.accent))state.preferences.accent=pref.accent;
    if(typeof pref.profile_name==='string')state.preferences.profile_name=pref.profile_name;
  } else if(type==='pedido_enviado') {
    const rawKind=String(msg.kind||msg.tipo||'');
    const kind=({chat:'texto',panel_action:'acao',quick_action:'acao',playlist_request:'playlist'}[rawKind]||rawKind);
    const prior=state.pending[id];
    const delivery=msg.accepted===true?'accepted':prior?.state||'sending';
    state.pending[id]={...prior,kind,state:delivery,conversation_id:String(msg.conversation_id||state.conversations.active_id||'')};
    if(msg.action)state.pending[id].action=String(msg.action);
    if(msg.text) {
      state.pending[id].text=String(msg.text);
      state.pending[id].messageAdded=true;
      upsertMessage({id,role:'user',text:String(msg.text),conversation_id:state.pending[id].conversation_id,delivery:delivery==='accepted'?'accepted':'pending'});
    }
    if(kind==='texto'&&!['responded','failed'].includes(delivery))armPendingTimer(id);
  } else if(type==='input_ack') {
    if(msg.accepted===true) {
      if(id)(state.pending[id]||(state.pending[id]={})).state='accepted';
      if(state.pending[id]?.kind==='texto')armPendingTimer(id);
      for(const m of state.messages)if(m.id===id&&m.role==='user')m.delivery='accepted';
    } else {const text=String(msg.message||'A mente recusou o pedido.');failPending(id,text);toast(text);}
  } else if(type==='assistant_message') {
    const pending=state.pending[id];
    clearTimeout(pendingTimers.get(id));pendingTimers.delete(id);
    const cid=String(msg.conversation_id||pending?.conversation_id||state.conversations.active_id||'');
    upsertMessage({id,role:'assistant',text:String(msg.text||''),timestamp:msg.timestamp,conversation_id:cid});
    for(const m of state.messages)if(m.id===id&&m.role==='user')m.delivery='responded';
    if(id)(pending||(state.pending[id]={})).state='responded';
    if(msg.emotion)state.emotion=String(msg.emotion);
  } else if(type==='state') {
    repaint=applyState(msg)||!!msg.event;
    if(msg.event)state.events.push(msg.event);
  } else if(type==='dashboard_state') {
    if(msg.dashboard&&typeof msg.dashboard==='object')state.dashboard=msg.dashboard;
  } else if(type==='conversations_state') {
    if(msg.conversations)setConversationSnapshot(msg.conversations,msg.success===true&&['create','select','delete','list'].includes(msg.action));
    if(id)(state.pending[id]||(state.pending[id]={})).state=msg.success?'confirmed':'failed';
    if(msg.success&&['create','select','delete'].includes(msg.action)){state.page='chat';state.mode='full';}
    if(!msg.success)toast(msg.message||'A conversa não foi alterada.');
  } else if(type==='mode_state'||type==='mode_result') {
    if(['chat','voice'].includes(msg.mode))state.interactionMode=msg.mode;
    if(typeof msg.voice_available==='boolean')state.voiceAvailable=msg.voice_available;
    if(id)(state.pending[id]||(state.pending[id]={})).state=msg.success?'confirmed':'failed';
    if(msg.success===false)toast(msg.message||'A troca de modo não foi confirmada.');
  } else if(type==='settings_state'||type==='settings_result') {
    if(msg.settings&&typeof msg.settings==='object')state.settings=msg.settings;
    if(type==='settings_result') {
      resetFields=true;
      for(const el of document.querySelectorAll('input[type=password]'))el.value='';
      if(id)(state.pending[id]||(state.pending[id]={})).state=msg.saved?'confirmed':'failed';
      toast(msg.message||(msg.saved?'Configuração salva.':'A configuração não foi salva.'));
    }
  } else if(type==='action_state'||type==='panel_action_state') {
    const action=String(msg.action||state.pending[id]?.action||'');
    state.actions[action]={state:msg.state,summary:msg.summary||'',id};
    if(id)(state.pending[id]||(state.pending[id]={})).state=String(msg.state||'');
    if(['failed','partial','awaiting_confirmation'].includes(msg.state))toast(msg.summary||({failed:'A ação falhou.',partial:'A ação foi parcialmente concluída.',awaiting_confirmation:'Aguardando sua confirmação.'}[msg.state]));
  } else if(type==='restart_result') {
    if(id)(state.pending[id]||(state.pending[id]={})).state=msg.accepted?'accepted':'failed';
    toast(msg.message||(msg.accepted?'Reinício solicitado.':'O reinício não foi aceito.'));
  } else if(type==='playlist_result'||type==='dev_query_result'||type==='dev_control_result') {
    if(id)(state.pending[id]||(state.pending[id]={})).state=msg.result?.ok===false?'failed':'confirmed';
  } else if(type==='error'||type==='erro_interface') {
    const text=String(msg.message||'O pedido não pôde ser concluído.');
    failPending(id,text);toast(text);
  }
  for(const fn of subscribers) {try{fn(msg);}catch(error){console.error('Falha ao apresentar evento:',error);}}
  // A observação é consumida integralmente. A pintura só é invalidada se essa
  // região estiver visível; recibos e mensagens continuam sendo aplicados agora.
  if(type==='music_meter')repaint=false; // o componente de áudio projeta suas barras localmente
  if(type==='dev_events')repaint=state.mode==='full'&&state.page==='dev';
  if(type==='dashboard_state')repaint=state.mode==='quick'||(state.mode==='full'&&state.page!=='chat');
  if(repaint)scheduleRender();
}
function onEvent(fn) {
  subscribers.add(fn);
  for(const event of eventReplay)try{fn(event);}catch(error){console.error('Falha ao apresentar histórico de eventos:',error);}
  return()=>subscribers.delete(fn);
}
function confirmDialog(title,copy,onAccept,options={}) {
  const dialog=document.getElementById('confirm-dialog'),input=document.getElementById('confirm-input');
  document.getElementById('confirm-title').textContent=String(title);
  document.getElementById('confirm-copy').textContent=String(copy);
  input.hidden=!options.input;input.value=options.value||'';
  document.getElementById('confirm-accept').textContent=options.label||'Confirmar';
  confirmation=onAccept;dialog.showModal();
  if(options.input)input.focus();
}
function closeDialog() {document.getElementById('confirm-dialog')?.close();confirmation=null;}
async function sendMessage() {
  const text=state.draft.trim();if(!text||!state.connected)return;
  const id=await request('texto',{text});
  if(!id)return;
  state.pending[id].text=text;
  state.draft='';if(state.mode==='full')state.page='chat';
  render();scrollChat();document.getElementById('composer-input')?.focus();
}
function conversationMenu(id) {
  const item=list(state.conversations.items).find(c=>String(c.id)===id);if(!item)return;
  const dialog=document.getElementById('confirm-dialog');
  confirmDialog('Opções da conversa',item.title||'Conversa',()=>{}, {label:'Fechar'});
  const actions=document.createElement('div');actions.className='dialog-actions';
  for(const [operation,label] of [['rename','Renomear'],[item.pinned?'unpin':'pin',item.pinned?'Desafixar':'Fixar'],[item.status==='archived'?'unarchive':'archive',item.status==='archived'?'Restaurar':'Arquivar'],['delete','Excluir']]) {
    const button=document.createElement('button');button.className='secondary';button.textContent=label;
    button.addEventListener('click',()=>{
      closeDialog();actions.remove();
      if(operation==='rename')confirmDialog('Renomear conversa','Novo título da conversa:',title=>request('conversa',{operation:'rename',conversation_id:id,title}),{input:true,value:item.title||'',label:'Renomear'});
      else if(operation==='delete')confirmDialog('Excluir conversa','Excluir este chat e todo o contexto dele? As memórias globais e ações já executadas serão preservadas.',()=>request('conversa',{operation:'delete',conversation_id:id}),{label:'Excluir'});
      else request('conversa',{operation:operation==='unpin'?'pin':operation,conversation_id:id,pinned:operation==='pin'});
    });
    actions.appendChild(button);
  }
  dialog.querySelector('.dialog-actions').before(actions);
  dialog.addEventListener('close',()=>actions.remove(),{once:true});
}
function start() {
  if(started)return;started=true;
  document.addEventListener('submit',event=>{
    if(!event.target.matches('[data-composer]'))return;
    event.preventDefault();sendMessage();
  });
  document.addEventListener('input',event=>{
    if(event.target.matches('#composer-input'))state.draft=event.target.value;
  });
  document.addEventListener('compositionstart',()=>{composing=true;});
  document.addEventListener('compositionend',()=>{composing=false;scheduleRender();});
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button||button.disabled)return;
    if(button.dataset.mode){goMode(button.dataset.mode);return;}
    if(button.dataset.page){goPage(button.dataset.page);return;}
    if(button.dataset.voice){request('voz',{mode:button.dataset.voice});return;}
    if(button.dataset.conversation){request('conversa',{operation:'select',conversation_id:button.dataset.conversation});return;}
    if(button.dataset.conversationMenu){conversationMenu(button.dataset.conversationMenu);return;}
    if(button.dataset.retry) {
      const m=state.messages.find(m=>m.id===button.dataset.retry&&m.role==='user');
      if(m){state.draft=m.text;render();document.getElementById('composer-input')?.focus();}
      return;
    }
    if(button.id==='confirm-accept') {
      const callback=confirmation,value=document.getElementById('confirm-input').value.trim();
      closeDialog();if(callback)callback(value);return;
    }
    const action=button.dataset.action;
    if(action==='close-dialog'){closeDialog();return;}
    if(action==='new-conversation'){request('conversa',{operation:'create',title:'Nova conversa'});return;}
    if(action==='voice'){request('voz',{mode:state.interactionMode==='voice'?'chat':'voice'});return;}
    if(action==='music-toggle') {
      const music=object(state.dashboard.music),playing=music.state==='playing';
      if(!state.connected||music.controls_available!==true||music.freshness==='unavailable')return;
      request('acao',{action:'media_toggle',request:playing?'pausa a música':'continua a música',payload:{command:playing?'pause':'play'}});
    }
  });
  render();
  if(window.qt?.webChannelTransport&&typeof QWebChannel==='function') {
    new QWebChannel(qt.webChannelTransport,channel=>{
      bridge=channel.objects.laylay;
      if(!bridge){toast('A ponte da interface não foi registrada.');return;}
      bridge.evento.connect(receiveEvent);
      bridge.pronto();
    });
  } else toast('A interface oficial precisa da ponte local da Laylay.');
}
window.addEventListener('pagehide',()=>{
  if(renderFrame)cancelAnimationFrame(renderFrame);
  for(const timer of pendingTimers.values())clearTimeout(timer);
  pendingTimers.clear();clearTimeout(toastTimer);avatarMotion.stop();
},{once:true});
paths.mic='<path d="M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0ZM5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>';
paths.more='<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>';
window.LaylayInterface={state,icon,escapeHTML,pageHeading,avatar,status,compose,musicCard,render,invalidate:scheduleRender,goPage,goMode,toast,request,views,onEvent,receiveEvent,confirm:confirmDialog,safeArtwork};
const avatarMotion=(()=>{
 const reducedQuery=window.matchMedia('(prefers-reduced-motion: reduce)');
 const hoverQuery=window.matchMedia('(any-hover: hover) and (any-pointer: fine)');
 let avatars=[],frame=0,blinkTimer=0,lastFrame=0,targetsDirty=true,pointer=null,environment='';
 let focused=document.hasFocus();
 const canAnimate=()=>!state.preferences.reduced&&!reducedQuery.matches&&!document.hidden&&focused&&state.windowVisible;
 const clamp=value=>Math.max(-1,Math.min(1,value));
 function paint(avatar){
  avatar.el.style.setProperty('--look-x',avatar.x.toFixed(3)+'px');
  avatar.el.style.setProperty('--look-y',avatar.y.toFixed(3)+'px');
 }
 function neutralize(){
  for(const avatar of avatars){avatar.x=avatar.y=avatar.tx=avatar.ty=0;avatar.el.classList.remove('is-blinking');paint(avatar)}
 }
 function stop(){
  if(frame)cancelAnimationFrame(frame);
  clearTimeout(blinkTimer);frame=blinkTimer=lastFrame=0;
  for(const avatar of avatars)avatar.el.classList.remove('is-blinking');
 }
 function updateTargets(){
  targetsDirty=false;
  for(const avatar of avatars){
   if(!pointer||!hoverQuery.matches){avatar.tx=avatar.ty=0;continue}
   const rect=avatar.el.getBoundingClientRect();
   const width=avatar.el.offsetWidth,height=avatar.el.offsetHeight;
   const dx=pointer.x-(rect.left+rect.width/2),dy=pointer.y-(rect.top+rect.height/2);
   avatar.tx=clamp(dx/Math.max(170,width*3.3))*width*.075;
   avatar.ty=clamp(dy/Math.max(145,height*3))*height*.048;
  }
 }
 function tick(now){
  frame=0;
  if(!canAnimate()){neutralize();lastFrame=0;return}
  if(targetsDirty)updateTargets();
  const elapsed=lastFrame?Math.min(48,now-lastFrame):16;
  const blend=1-Math.exp(-elapsed/85);
  lastFrame=now;
  let moving=false;
  for(const avatar of avatars){
   const dx=avatar.tx-avatar.x,dy=avatar.ty-avatar.y;
   if(Math.abs(dx)>.012||Math.abs(dy)>.012){avatar.x+=dx*blend;avatar.y+=dy*blend;moving=true}
   else{avatar.x=avatar.tx;avatar.y=avatar.ty}
   paint(avatar);
  }
  if(moving)frame=requestAnimationFrame(tick);else lastFrame=0;
 }
 function requestTick(){if(canAnimate()&&avatars.length&&!frame)frame=requestAnimationFrame(tick)}
 function scheduleBlink(delay=2600+Math.random()*2600){
  clearTimeout(blinkTimer);blinkTimer=0;
  if(!canAnimate()||!avatars.length)return;
  blinkTimer=setTimeout(()=>closeEyes(Math.random()<.16?2:1),delay);
 }
 function closeEyes(remaining){
  blinkTimer=0;if(!canAnimate())return;
  for(const avatar of avatars)avatar.el.classList.add('is-blinking');
  blinkTimer=setTimeout(()=>{
   blinkTimer=0;
   for(const avatar of avatars)avatar.el.classList.remove('is-blinking');
   if(!canAnimate())return;
   if(remaining>1)blinkTimer=setTimeout(()=>closeEyes(remaining-1),170);
   else scheduleBlink();
  },115);
 }
 function resetLook(){pointer=null;targetsDirty=true;if(canAnimate())requestTick();else neutralize()}
 function refresh(){
  focused=document.hasFocus();
  const elements=Array.from(document.querySelectorAll('.avatar')).filter(el=>el.offsetWidth&&el.offsetHeight);
  const reduced=state.preferences.reduced||reducedQuery.matches;
  document.body.classList.toggle('avatar-motion-off',reduced);
  document.body.classList.toggle('avatar-motion-paused',document.hidden||!focused);
  const nextEnvironment=[reduced,document.hidden,focused,state.windowVisible].join(':');
  if(environment===nextEnvironment&&elements.length===avatars.length&&elements.every((el,i)=>el===avatars[i].el))return;
  stop();environment=nextEnvironment;
  const existing=new Map(avatars.map(avatar=>[avatar.el,avatar]));
  avatars=elements.map(el=>existing.get(el)||({el,x:0,y:0,tx:0,ty:0}));
  neutralize();targetsDirty=true;
  if(!canAnimate()){pointer=null;return}
  if(pointer&&hoverQuery.matches)requestTick();
  scheduleBlink(1500+Math.random()*1300);
 }
 window.addEventListener('pointermove',event=>{
  if(focused!==document.hasFocus())refresh();
  if(event.pointerType!=='mouse'||!hoverQuery.matches||!canAnimate())return;
  pointer={x:event.clientX,y:event.clientY};targetsDirty=true;requestTick();
 },{passive:true});
 document.documentElement.addEventListener('pointerleave',resetLook,{passive:true});
 window.addEventListener('blur',()=>{focused=false;pointer=null;refresh()});
 window.addEventListener('focus',()=>{focused=true;refresh()});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pointer=null;refresh()});
 function geometryChanged(){if(pointer){targetsDirty=true;requestTick()}}
 window.addEventListener('resize',geometryChanged,{passive:true});
 document.addEventListener('scroll',geometryChanged,{passive:true,capture:true});
 reducedQuery.addEventListener('change',refresh);
 hoverQuery.addEventListener('change',()=>{pointer=null;refresh()});
 return {refresh,stop};
})();

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();

