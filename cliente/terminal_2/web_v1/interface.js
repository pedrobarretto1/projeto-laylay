// Interface oficial: apresenta somente eventos e dados da ponte local.
const paths={home:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',chat:'<path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-10a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8Z"/><path d="M7 10h8M7 14h5"/>',music:'<path d="M9 17V5l11-2v12M9 8l11-2"/><ellipse cx="6" cy="17.5" rx="3" ry="2.5"/><ellipse cx="17" cy="15.5" rx="3" ry="2.5"/>',lamp:'<path d="M8 14h8l4-5H4l4 5ZM12 14v6M7 21h10M8 9l1-6h6l1 6"/>',memory:'<path d="M7 4h12v17H7a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3ZM7 4v17M10 8h5M10 12h5"/>',system:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4M6 11h3l2-4 3 7 2-3h2"/>',settings:'<path d="m9 3-1 3-3 1 1 3-2 2 2 2-1 3 3 1 1 3h3l1-3 3-1 1-3 3-1v-3l-3-1-1-3-3-1-1-3Z"/><circle cx="11" cy="12" r="3"/>',chevron:'<path d="m9 5 7 7-7 7"/>',arrow:'<path d="M4 12h15m-5-5 5 5-5 5"/>',expand:'<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',collapse:'<path d="M4 8h4V4M20 8h-4V4M4 16h4v4M20 16h-4v4"/>',minus:'<path d="M5 12h14"/>',close:'<path d="m6 6 12 12M6 18 18 6"/>',play:'<path d="m8 5 11 7-11 7Z"/>',pause:'<path d="M8 5h2v14H8zM14 5h2v14h-2z"/>',next:'<path d="m5 5 10 7L5 19ZM18 5v14"/>',prev:'<path d="m19 5-10 7 10 7ZM6 5v14"/>',spark:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>',send:'<path d="M12 19V5m-5 5 5-5 5 5"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',check:'<path d="m5 12 4 4L19 6"/>',shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',heart:'<path d="M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8 6l8 8 8-8a5 5 0 0 0 0-7Z"/>',island:'<rect x="3" y="8" width="18" height="8" rx="4"/><path d="M8 12h2M14 12h2"/>',panel:'<rect x="6" y="3" width="12" height="18" rx="3"/><path d="M10 7h4M10 17h4"/>',full:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 4v16"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',refresh:'<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',volume:'<path d="m11 5-6 4H2v6h3l6 4ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>',leaf:'<path d="M20 3s-12-1-15 7a7 7 0 0 0 9 9C21 16 20 3 20 3ZM5 20l10-10"/>',calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 11h18M8 15h2"/>'};
paths.streaming='<rect x="3" y="4" width="18" height="13" rx="2"/><path d="m10 8 5 3-5 3ZM8 21h8M12 17v4"/>';
paths.dev='<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 16h4"/>';
const icon=(n)=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[n]||paths.spark)+'</svg>';

(() => {
'use strict';
const state = {
  mode:new URLSearchParams(window.location.search).get('presentation')==='desktop'?'desktop':'full',page:'home',connected:false,activity:'reconnecting',activityLabel:'Reconectando',
  emotion:'calma',emotionLevel:1,interactionMode:'chat',voiceAvailable:false,microphoneLevel:0,messages:[],
  draft:'',dashboard:{},settings:{},conversations:{active_id:'',items:[]},events:[],
  preferences:{reduced:false,mascot:true,accent:'violet',sidebar:true,home:{version:1,period_days:30,pinned_ids:[],hidden_ids:[]}},pending:{},
  actions:{},windowVisible:true,nativeWindow:false,availableWidth:0,availableHeight:0,desktopState:'compact',desktopMaterial:'fallback',desktopPinned:false,desktopView:'overview',desktopPhase:'idle',desktopTransition:0,desktopTargetWidth:0,desktopTargetHeight:0,streamingOpen:false,streamingExpanded:false
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
const locationScroll=new Map();
const presentationLocation=()=>state.mode+':'+(state.mode==='desktop'?state.desktopView+':':'')+state.page;
let presentationAckFrame=0,presentationAckKey='',streamingViewportFrame=0,streamingViewportElement=null,streamingViewportObserver=null;
let desktopDrag=null,suppressDesktopClick=false;
// Motion M2: transições discretas, somente após o ACK da geometria do Qt.
// A referência da página só é atualizada em estado idle, evitando flashes
// durante resize, conversas em streaming ou mudanças de snapshot.
let motionLocation='',motionDesktopState='compact';
let motionRunCount=0;
function motionAllowed() {
  return !state.preferences.reduced &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
function animateSafe(element,keyframes,options) {
  if(!element||!motionAllowed()||typeof element.animate!=='function')return null;
  // Evita animações concorrentes quando o usuário navega rapidamente.
  for(const anim of element.getAnimations())if(anim.effect?.target===element)anim.cancel();
  return element.animate(keyframes,{fill:'none',...options});
}
function animateDesktopMotion(location) {
  if(state.mode!=='desktop') {
    motionLocation='';motionDesktopState='compact';return;
  }
  if(state.desktopPhase!=='idle')return;
  const prior=motionLocation,oldState=motionDesktopState;
  motionLocation=location;motionDesktopState=state.desktopState;
  if(!motionAllowed())return;
  const island=document.querySelector('.desktop-island');
  if(!island)return;
  const expanded=state.desktopState==='expanded';
  if(expanded&&oldState!=='expanded') {
    // Motion compositor-friendly: a WebView é redimensionada pelo Qt antes
    // do efeito. Evitar animar o scroll container ou vários cartões grandes.
    const small=island.querySelector(
      state.desktopView==='page'?'.desktop-page .context-bar':'.desktop-overview .desktop-presence-copy');
    animateSafe(small,
      [{opacity:.45,transform:'translateY(9px)'},{opacity:1,transform:'translateY(0)'}],
      {duration:215,easing:'cubic-bezier(.2,.75,.25,1)'});
    animateSafe(island.querySelector('.desktop-wordmark'),
      [{opacity:.55,transform:'translateY(6px)'},{opacity:1,transform:'translateY(0)'}],
      {duration:180,delay:20,easing:'cubic-bezier(.2,.75,.25,1)'});
    motionRunCount++;return;
  }
  if(!expanded&&oldState==='expanded') {
    animateSafe(island.querySelector('.desktop-compact-copy'),
      [{opacity:.55,transform:'translateX(-7px)'},{opacity:1,transform:'translateX(0)'}],
      {duration:190,easing:'cubic-bezier(.2,.78,.2,1)'});
    animateSafe(island.querySelector('.desktop-miniature'),
      [{transform:'scale(.92)'},{transform:'scale(1)'}],
      {duration:210,easing:'cubic-bezier(.2,.78,.2,1)'});
    motionRunCount++;return;
  }
  if(expanded&&prior!==location) {
    // Sem transformar a viewport scrollável inteira; ela contém gráficos,
    // capas e painéis complexos, caros de rasterizar em cada quadro.
    const oldPage=prior.split(':').at(-1),currentPage=location.split(':').at(-1);
    const before=pages.findIndex(([id])=>id===oldPage);
    const after=pages.findIndex(([id])=>id===currentPage);
    const direction=before<0||after>=before?1:-1;
    const heading=island.querySelector(state.desktopView==='page'
      ?'.desktop-page .context-bar':'.desktop-overview .desktop-presence-copy');
    animateSafe(heading,
      [{opacity:.42,transform:'translateX('+(direction*17)+'px)'},{opacity:1,transform:'translateX(0)'}],
      {duration:215,easing:'cubic-bezier(.2,.78,.2,1)'});
    if(state.desktopView==='page'&&state.page!=='chat') {
      animateSafe(island.querySelector('.desktop-page-content .page-heading'),
        [{opacity:.6,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],
        {duration:200,delay:25,easing:'cubic-bezier(.2,.78,.2,1)'});
    }
    motionRunCount++;
  }
}

const escapeHTML=(v)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const object=(v)=>v&&typeof v==='object'&&!Array.isArray(v)?v:{};
const list=(v)=>Array.isArray(v)?v:[];
function avatar(size='') {
  const classes=String(size).replace(/[^a-zA-Z0-9 _-]/g,'');
  // Emoção é uma projeção do retrato canônico recebido; atividade e gestos
  // permanecem modificadores visuais, sem interpretar texto nem criar TTL.
  const emotion=state.connected?String(state.emotion||'calma'):'neutra';
  const key=emotion.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const expression=({alegre:'feliz',feliz:'feliz',animada:'animada',animado:'animada',empolgada:'animada',entusiasmada:'animada',debochada:'animada',curiosa:'curiosa',curioso:'curiosa',confusa:'confusa',confuso:'confusa',triste:'triste',brava:'brava',bravo:'brava',irritada:'brava',irritado:'brava',surpresa:'surpresa',surpreso:'surpresa',envergonhada:'envergonhada',envergonhado:'envergonhada'})[key]||'neutra';
  const level=state.connected?Math.max(1,Math.min(3,Math.round(Number(state.emotionLevel)||1))):1;
  const activity=state.connected?String(state.activity||'idle'):'reconnecting';
  const feeling=({listening:'hearing',thinking:'thinking',speaking:'speaking'})[activity]||'';
  return '<div class="avatar '+classes+' '+feeling+'" data-emotion="'+escapeHTML(emotion)+'" data-expression="'+expression+'" data-emotion-level="'+level+'" data-activity="'+escapeHTML(activity)+'" aria-hidden="true"><div class="mascot-figure"><div class="avatar-body"></div><i class="mascot-tuft"></i><i class="mascot-mark"></i><div class="face"><i class="eye"></i><i class="eye right"></i><i class="smile"></i><i class="cheek"></i><i class="cheek right"></i><i class="mascot-brow"></i><i class="mascot-brow right"></i></div><span class="mascot-emote"></span></div><i class="mascot-activity"></i></div>';
}
// Conexão da ponte não comprova disponibilidade da mente ou dos serviços.
function connectionStatus() {
  if(!state.connected)return {label:'Reconectando',kind:'offline',detail:'Ponte desconectada'};
  const health=object(object(state.dashboard).health);
  const model=object(health.llm);
  const modelKnown=Object.keys(model).length>0;
  const unavailable=modelKnown&&(model.freshness==='unavailable'||/indispon[ií]vel|falha|erro|offline/i.test(String(model.label||'')));
  const inProgress=['speaking','listening','thinking','executing'].includes(state.activity);
  const label=inProgress?(state.activityLabel||'Laylay em atividade'):unavailable?'Modelo indisponível':modelKnown?(state.activityLabel||'Ponte conectada'):'Ponte conectada';
  const published=Object.keys(health).length>0;
  const detail=['Ponte conectada',modelKnown?'Modelo: '+(model.label||'sem estado publicado'):'Modelo: sem leitura'];
  if(published)for(const [key,name] of [['memory','Memória'],['microphone','Microfone']]) {
    const item=object(health[key]);
    detail.push(name+': '+(item.label||'sem leitura'));
  }
  return {label,kind:unavailable?'warning':'online',detail:detail.join(' · ')};
}
function status() {
  const indicator=connectionStatus();
  return '<span class="status '+(indicator.kind==='online'?'':indicator.kind)+'" title="'+escapeHTML(indicator.detail)+'"><i></i>'+escapeHTML(indicator.label)+'</span>';
}
// Atualização pontual: telemetria pode mudar no chat sem remontar balões/inputs.
function refreshStatusNodes() {
  const indicator=connectionStatus();
  for (const element of document.querySelectorAll('span.status')) {
    element.classList.toggle('offline',indicator.kind==='offline');
    element.classList.toggle('warning',indicator.kind==='warning');
    element.title=indicator.detail;
    const label=Array.from(element.childNodes).find(node=>node.nodeType===3);
    if(label) {
      if(label.nodeValue!==indicator.label)label.nodeValue=indicator.label;
    } else element.appendChild(document.createTextNode(indicator.label));
  }
}
function operationalStrip() {
  const health=object(object(state.dashboard).health);
  const items=[
    ['Ponte',state.connected?'Conectada':'Desconectada'],
    ['Modelo',object(health.llm).label||'Sem leitura'],
    ['Memória',object(health.memory).label||'Sem leitura'],
    ['Microfone',object(health.microphone).label||'Sem leitura'],
  ];
  return '<div class="operational-strip" role="status" aria-label="Estado observado dos serviços">'+items.map(([name,value],index)=>'<span class="operational-item"><small>'+escapeHTML(name)+'</small><strong class="'+((index===0&&!state.connected)||/indispon[ií]vel|erro|falha/i.test(value)?'operational-unavailable':'')+'">'+escapeHTML(value)+'</strong></span>').join('')+'</div>';
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
  const pref=homePreferences(),d=object(state.dashboard),data=object(d.home),period=object(object(data.periods)[String(pref.period_days)]),m=object(d.music);
  const catalog=list(m.catalog),hidden=new Set(pref.hidden_ids),ranked=data.freshness==='unavailable'?[]:list(period.playlists).filter(item=>item&&Number(item.confirmed_plays)>0);
  const actions=data.freshness==='unavailable'?[]:list(period.actions).filter(item=>homeAction(item.id)&&Number(item.confirmed_uses)>0);
  const now=new Date(),hour=now.getHours(),name=profileName(),greeting=hour<12?'Bom dia':hour<18?'Boa tarde':'Boa noite';
  const day=now.toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'}),last=activeMessages().at(-1),conversation=list(state.conversations.items).find(item=>item.id===state.conversations.active_id);
  const musicVisible=Boolean(m.title)&&m.freshness!=='unavailable',resume=Boolean(last||conversation||musicVisible),hasHistory=ranked.length+actions.length>0;
  const sectionHead=(title,extra='')=>'<div class="section-head"><h2>'+escapeHTML(title)+'</h2>'+extra+'</div>';
  const controls=(id,reason)=>'<button class="icon-button" data-home-why="'+escapeHTML(id)+'" data-reason="'+escapeHTML(reason)+'" aria-label="Por que apareceu?" title="Por que apareceu?">'+icon('info')+'</button><button class="icon-button '+(pref.pinned_ids.includes(id)?'is-pinned':'')+'" data-home-pin="'+escapeHTML(id)+'" aria-label="'+(pref.pinned_ids.includes(id)?'Desafixar':'Fixar')+'" title="'+(pref.pinned_ids.includes(id)?'Desafixar':'Fixar')+'">'+icon('pin')+'</button><button class="icon-button" data-home-hide="'+escapeHTML(id)+'" aria-label="Ocultar sugestão" title="Ocultar sugestão">'+icon('close')+'</button>';
  const artwork=(url,title)=>{const safe=safeArtwork(url);return '<div class="cover">'+(safe?'<img src="'+escapeHTML(safe)+'" alt="">':'<span>'+escapeHTML((title||'♪').slice(0,1))+'</span>')+'</div>';};
  const playlists=ranked.filter(item=>!hidden.has('playlist:'+item.name));
  // Capas reais vêm exclusivamente do catálogo observado. Sem capa, mostra arte abstrata local.
  function playlistShowcaseCard(item,position,featured=false,fromRanking=true) {
    const found=catalog.find(entry=>entry.name===item.name);
    const name=String(item.name||'Playlist sem nome');
    const id='playlist:'+name, pinned=pref.pinned_ids.includes(id);
    const count=Number(item.confirmed_plays)||0;
    const catalogCount=Number(found?.count);
    const available=state.connected&&Boolean(found)&&m.catalog_play_available===true;
    const label=fromRanking
      ?(featured?'MAIS PRESENTE NESTE PERÍODO':'ENTRE AS MAIS OUVIDAS')
      :(featured?'DA SUA BIBLIOTECA':'PARA REDESCOBRIR');
    const detail=fromRanking
      ?count+' '+(count===1?'reprodução iniciada confirmada':'reproduções iniciadas confirmadas')
      :(Number.isFinite(catalogCount)&&catalogCount>=0
        ?catalogCount+' '+(catalogCount===1?'faixa na biblioteca':'faixas na biblioteca')
        :'Disponível na sua biblioteca');
    const why=fromRanking?controls(id,item.reason||'Reproduções iniciadas e confirmadas nos últimos '+pref.period_days+' dias.'):
      '<button class="spotlight-pin '+(pinned?'is-pinned':'')+'" data-home-pin="'+escapeHTML(id)+'" aria-label="'+(pinned?'Desafixar ':'Fixar ')+escapeHTML(name)+'" aria-pressed="'+pinned+'" title="'+(pinned?'Desafixar':'Fixar')+'">'+icon('pin')+'</button>';
    const play=available?
      '<button class="showcase-play" data-tp-action="playlist-play" data-name="'+escapeHTML(name)+'" aria-label="Tocar '+escapeHTML(name)+'">'+icon('play')+(featured?'<span>Ouvir agora</span>':'')+'</button>':
      fromRanking?'<button class="showcase-play" data-tp-action="playlist-play" data-name="'+escapeHTML(name)+'" aria-label="Reprodução indisponível para '+escapeHTML(name)+'" title="A reprodução ainda não foi confirmada pela biblioteca" disabled>'+icon('play')+(featured?'<span>Indisponível</span>':'')+'</button>':
      '<button class="showcase-play showcase-open" data-page="music" aria-label="Abrir Música para ver '+escapeHTML(name)+'">'+icon('music')+'<span>'+(featured?'Ver na Música':'Ver')+'</span></button>';
    return '<article class="playlist-card playlist-showcase-card '+(featured?'playlist-spotlight':'playlist-tile')+'" data-render-key="home-playlist:'+escapeHTML(name)+'"><div class="showcase-cover">'+artwork(found?.artwork_url,name)+'</div><div class="playlist-info"><div class="showcase-kicker">'+(fromRanking?'<span class="showcase-rank">'+(position+1)+'</span>':'')+escapeHTML(label)+'</div><strong title="'+escapeHTML(name)+'">'+escapeHTML(name)+'</strong><p>'+escapeHTML(detail)+'</p></div><div class="playlist-buttons">'+why+play+'</div></article>';
  }
  const playlistRows=playlists.length
    ?playlistShowcaseCard(playlists[0],0,true)
      +(playlists.length>1?'<div class="playlist-showcase-grid">'+playlists.slice(1,4).map((item,index)=>playlistShowcaseCard(item,index+1)).join('')+'</div>':'')
      +(playlists.length>4?'<button class="showcase-library-link" data-page="music">Explorar a biblioteca '+icon('arrow')+'</button>':'')
    :'';
  const actionItems=actions.length?actions:list(d.quick_actions).filter(item=>homeAction(item.id)).map(item=>({...item,shortcut:true}));
  const frequent=actionItems.filter(item=>!hidden.has('action:'+item.id)).map(item=>{const action=homeAction(item.id);return '<article class="home-action-item"><button class="quick-action" data-home-execute="action:'+escapeHTML(item.id)+'" '+(!action.available?'disabled':'')+'>'+icon(action.icon)+'<span><strong>'+escapeHTML(action.title)+'</strong><small>'+escapeHTML(item.shortcut?'Acesso rápido · você escolhe quando usar':item.confirmed_uses+' usos confirmados · '+(action.page?'abrir controles':'neste período'))+'</small></span></button><div class="home-action-tools">'+controls('action:'+item.id,item.reason||(item.shortcut?'Atalho publicado pela Laylay. Ainda não há histórico suficiente para um ranking.':'Execuções confirmadas nos últimos '+pref.period_days+' dias.'))+'</div></article>';}).join('');
  // Uma preferência fixada não desaparece apenas porque o catálogo está offline.
  const availablePins=pref.pinned_ids.map(id=>{
    if(id.startsWith('playlist:')) {
      const title=id.slice(9),pl=catalog.find(item=>item.name===title);
      return {id,title,playlist:true,artwork_url:pl?.artwork_url||'',count:pl?.count,
        known:Boolean(pl),available:state.connected&&Boolean(pl)&&m.catalog_play_available===true};
    }
    if(id.startsWith('action:')) {
      const action=homeAction(id.slice(7));
      return action?{id,...action,playlist:false}:null;
    }
    return null;
  }).filter(Boolean);
  const pins=availablePins.map(item=>{
    const title=String(item.title||'Atalho');
    const safe= item.playlist?safeArtwork(item.artwork_url):'';
    const cover=item.playlist
      ?'<div class="pinned-card-cover">'+(safe?'<img src="'+escapeHTML(safe)+'" alt="" loading="lazy">':'<span aria-hidden="true">'+escapeHTML(title.slice(0,1).toUpperCase()||'♪')+'</span>')+'</div>'
      :'<div class="pinned-card-cover pinned-action-cover">'+icon(item.icon||'spark')+'</div>';
    const count=Number(item.count);
    const subtitle=item.playlist
      ?(!item.known?'Biblioteca temporariamente indisponível':
        Number.isFinite(count)&&count>=0
          ?count+' '+(count===1?'faixa':'faixas')+' · fixada'
          :'Playlist fixada por você')
      :'Atalho fixado por você';
    const main=item.playlist
      ?(item.available
        ?'<button class="pinned-card-action pinned-card-play" data-tp-action="playlist-play" data-name="'+escapeHTML(title)+'" title="Tocar playlist" aria-label="Tocar '+escapeHTML(title)+'">'+icon('play')+'</button>'
        :'<button class="pinned-card-action" data-page="music" title="Ver na Música" aria-label="Abrir Música para '+escapeHTML(title)+'">'+icon('music')+'</button>')
      :'<button class="pinned-card-action" data-home-execute="'+escapeHTML(item.id)+'" title="'+escapeHTML(item.available?'Executar atalho':'Atalho indisponível')+'" aria-label="Executar '+escapeHTML(title)+'" '+(!item.available?'disabled':'')+'>'+icon(item.icon||'spark')+'</button>';
    return '<article class="pinned-mini-card" data-pinned-id="'+escapeHTML(item.id)+'">'+cover+
      '<div class="pinned-card-copy"><strong title="'+escapeHTML(title)+'">'+escapeHTML(title)+'</strong><small>'+escapeHTML(subtitle)+'</small></div>'+
      '<div class="pinned-card-actions">'+main+
      '<button class="pinned-card-action pinned-card-remove" data-home-pin="'+escapeHTML(item.id)+'" title="Desafixar" aria-label="Desafixar '+escapeHTML(title)+'">'+icon('close')+'</button></div></article>';
  }).join('');

  const routine=object(d.routines),agenda=(routine.freshness==='unavailable'?[]:list(routine.items)).slice(0,3).map(item=>'<div class="agenda-item"><time>'+escapeHTML(item.time||item.date||'—')+'</time><div><strong>'+escapeHTML(item.name||'Compromisso')+'</strong><p>'+escapeHTML(item.active===false?'Desativado':item.date||list(item.days).join(', ')||'Agenda publicada')+'</p></div></div>').join('');
  const context=object(m.context_music),moment=Boolean(context.summary)&&!hidden.has('moment:context_music');
  const shortlist=catalog.slice(0,3);
  const catalogCards=shortlist.length?playlistShowcaseCard(shortlist[0],0,true,false)
    +(shortlist.length>1?'<div class="playlist-showcase-grid">'+shortlist.slice(1).map((item,index)=>playlistShowcaseCard(item,index+1,false,false)).join('')+'</div>':''):'';

  return '<div class="page-content home-inteligente"><header class="home-welcome"><div class="home-mascot presence">'+avatar()+'</div><div><span class="eyebrow">UM ESPAÇO COM O SEU RITMO</span><h1>'+greeting+(name?', <span>'+escapeHTML(name)+'.</span>':'.')+'</h1><p>'+escapeHTML(hasHistory?'Com o que importa por perto.':'Seu Início ganha forma conforme você usa a Laylay.')+'</p></div><div class="date">'+escapeHTML(day)+'<span>'+status()+'</span></div></header>'+operationalStrip()+'<div class="home-layout"><div class="home-primary">'+
    (resume?'<section>'+sectionHead('Continuar de onde parou','<small>O que ficou por perto</small>')+'<div class="resume-grid">'+(last||conversation?'<article class="resume-card"><div class="resume-label">'+icon('chat')+' CONVERSA RECENTE</div><h3>'+escapeHTML(conversation?.title||'Nossa conversa')+'</h3><p class="home-resume-excerpt">'+escapeHTML(last?.text||'Seu histórico está disponível na conversa.')+'</p><button class="text-button" data-page="chat">Retomar conversa '+icon('arrow')+'</button></article>':'')+(musicVisible?'<article class="resume-card music music-card"><div class="resume-label">'+icon('music')+' SUA ÚLTIMA TRILHA</div><div class="music-resume">'+artwork(m.artwork_url,m.title)+'<div class="music-info"><h3>'+escapeHTML(m.title)+'</h3><p>'+escapeHTML(m.channel||'')+'</p></div><button class="round-play music-play" data-action="music-toggle" aria-label="'+(m.state==='playing'?'Pausar música':'Continuar música')+'" '+(!state.connected||m.controls_available!==true?'disabled':'')+'>'+icon(m.state==='playing'?'pause':'play')+'</button></div><div class="progress"><span style="width:'+(Number(m.duration_seconds)>0?Math.min(100,Math.max(0,100*Number(m.position_seconds||0)/Number(m.duration_seconds))):0)+'%"></span></div><p class="home-track-context">'+escapeHTML(m.playlist||'Reprodução observada')+'</p></article>':'')+'</div></section>':'')+
    (!hasHistory?'<section class="empty">'+icon('spark')+'<h2>Seu jeito, com o tempo.</h2><p>Ainda não há uso confirmado suficiente para organizar suas sugestões. Você pode conversar, explorar sua música e fixar atalhos.</p><button class="primary" data-page="chat">Começar uma conversa '+icon('arrow')+'</button></section>':'')+
    '<section><div class="section-head"><div><h2>Sua trilha favorita</h2><small>Reproduções iniciadas · últimos '+pref.period_days+' dias'+(data.freshness==='stale'?' · leitura anterior':'')+'</small></div><div class="segment" aria-label="Período do ranking">'+[7,30].map(days=>'<button data-home-period="'+days+'" class="'+(pref.period_days===days?'active':'')+'" aria-pressed="'+(pref.period_days===days)+'">'+days+' dias</button>').join('')+'</div></div><div class="playlist-ranking">'+(playlistRows||(!ranked.length&&!catalogCards?'<p class="help-line">Suas playlists aparecerão quando a biblioteca estiver disponível.</p>':ranked.length?'<p class="help-line">As sugestões deste período foram ocultadas.</p>':''))+'</div>'+(!ranked.length&&catalogCards?'<div class="home-catalog-showcase"><p class="showcase-empty-note">Ainda sem reproduções confirmadas neste período. Enquanto isso, conheça suas playlists.</p><div class="playlist-catalog-grid">'+catalogCards+'</div></div>':'')+'</section>'+
    '<section>'+sectionHead('Você usa bastante','<button class="text-button" data-page="system">Ver ações '+icon('arrow')+'</button>')+'<div class="quick-actions">'+(frequent||'<p class="help-line">Seus atalhos frequentes aparecem quando houver execuções confirmadas.</p>')+'</div></section></div><aside class="home-aside">'+
    '<section class="aside-moment"><span class="eyebrow">'+(moment?'PARA ESTE MOMENTO':'ESCOLHA O QUE FICA')+'</span><h3>'+escapeHTML(moment?'Encontre o seu ritmo.':'Comece pelos seus favoritos.')+'</h3><p>'+escapeHTML(moment?context.summary:'Fixe playlists e ações que quer encontrar aqui. Você continua escolhendo o que executar.')+'</p><div class="moment-actions"><button class="text-button" data-page="music">Abrir música '+icon('arrow')+'</button>'+(moment?'<button class="text-button" data-home-why="moment:context_music" data-reason="'+escapeHTML(context.recommendation||'Contexto musical publicado pela Laylay com base em '+list(context.basis).join(', '))+ '" aria-label="Por que esta sugestão apareceu?">'+icon('info')+'</button><button class="text-button" data-home-hide="moment:context_music" aria-label="Ocultar sugestão de momento">'+icon('close')+'</button>':'')+'</div></section>'+
    '<section>'+sectionHead('Seu dia','<small>Sua agenda</small>')+(agenda||'<p class="help-line">Nenhum compromisso publicado agora.</p>')+'<button class="text-button" data-page="lamp">Ver agenda '+icon('arrow')+'</button></section><section>'+sectionHead('Fixados por você','<small>Sempre por perto</small>')+'<div class="pinned-mini-list">'+(pins||'<div class="pinned-empty">'+icon('pin')+'<p>Fixe uma playlist ou ação para encontrá-la aqui.</p></div>')+'</div>'+(availablePins.some(item=>item.playlist)?'<button class="pinned-explore" data-page="music">Explorar biblioteca '+icon('arrow')+'</button>':'')+'</section></aside></div><footer class="home-controls"><span>Você escolhe o que fica por perto.</span><button class="text-button" data-home-restore>'+icon('refresh')+' Restaurar sugestões</button></footer></div>';
}
function homePreferences(){const value=object(state.preferences.home);return {version:1,period_days:value.period_days===7?7:30,pinned_ids:list(value.pinned_ids).filter(id=>typeof id==='string'),hidden_ids:list(value.hidden_ids).filter(id=>typeof id==='string')};}
function homeAction(id){
  const known={open_vscode:{title:'Abrir editor',icon:'dev',request:'abre o Visual Studio Code'},organize_desktop:{title:'Organizar desktop',icon:'system',request:'organiza o desktop automaticamente'},briefing:{title:'Briefing de hoje',icon:'calendar',request:'me passa o briefing de hoje'}};
  const navigation={iot_power:['Ver dispositivos','lamp'],iot_brightness:['Ajustar iluminação','lamp'],iot_status:['Estado dos dispositivos','lamp'],routine_cancel:['Ver agenda','lamp'],media_toggle:['Sua reprodução','music'],media_next:['Sua reprodução','music'],media_previous:['Sua reprodução','music'],media_repeat:['Opções de reprodução','music'],media_replay:['Sua reprodução','music'],volume_set:['Ajustar volume','music'],playlist_play:['Escolher uma playlist','music'],playlist_shuffle:['Explorar playlists','music'],audio_output_select:['Saída de áudio','music']};
  if(Object.hasOwn(navigation,id))return {title:navigation[id][0],page:navigation[id][1],icon:navigation[id][1],available:true};
  if(!Object.hasOwn(known,id))return null;
  const published=list(state.dashboard.quick_actions).find(item=>item.id===id);
  return {...known[id],available:state.connected&&published?.state==='available'};
}
function changeHomePreference(key,value){request('preferencia',{name:'inicio_inteligente',value:{...homePreferences(),[key]:value}});}
function chat() {
  const pending=Object.values(state.pending).some(p=>p.kind==='texto'&&p.conversation_id===state.conversations.active_id&&['sending','accepted'].includes(p.state));
  return '<section class="chat-view chat-layout">'+pageHeading('VAMOS CONVERSAR',conversationTitle(),'Pode deixar as ideias chegarem.')+'<div class="chat-history" id="chat-history" tabindex="0" role="region" aria-label="Histórico da conversa">'+messages()+'</div><div class="chat-status-line">'+(pending?'Aguardando a resposta da Laylay…':state.interactionMode==='voice'?(state.voiceAvailable?'Modo voz · microfone da Laylay':'Ouvido indisponível'):'')+'</div>'+compose()+'<p class="composer-note">'+escapeHTML(state.connected?'Conversa conectada à Laylay.':'Reconectando à Laylay.')+'</p></section>';
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
  return '<section class="window" aria-label="Interface completa"><aside class="sidebar"><div class="brand"><span class="mark" aria-hidden="true"></span>laylay</div><div class="nav-group-label">Por perto</div><nav class="nav" aria-label="Páginas da Laylay">'+pages.map(p=>(p[0]==='system'?'<div class="nav-group-label nav-advanced-label">Ferramentas</div>':'')+'<button class="'+(state.page===p[0]?'active':'')+'" data-page="'+p[0]+'" '+(state.page===p[0]?'aria-current="page"':'')+'>'+icon(p[0])+'<span>'+p[1]+'</span></button>').join('')+'</nav>'+conversationList()+'<div class="sidebar-foot"><span class="profile">'+escapeHTML(name.slice(0,1)||'U')+'</span><div><strong>'+escapeHTML(name||'Seu espaço')+'</strong><small>Laylay · interface 1.0</small></div><button class="icon-btn" data-page="settings" aria-label="Abrir configurações">'+icon('settings')+'</button></div></aside><div class="main"><div class="titlebar"><div class="breadcrumb"><span>Laylay</span>'+icon('chevron')+'<span>'+pageLabel()+'</span></div><div class="window-actions">'+voiceSwitch()+status()+'<span class="separator"></span><button class="icon-btn" data-mode="quick" aria-label="Recolher para painel rápido" title="Painel rápido">'+icon('collapse')+'</button><button class="icon-btn" data-mode="island" aria-label="Recolher para ilha" title="Recolher para ilha">'+icon('minus')+'</button></div></div><div class="page" id="page-content">'+content+'</div><footer class="main-footer"><span>'+icon('shield')+' Seu espaço, no seu tempo.</span><span class="right-footer bridge-label">'+escapeHTML(state.connected?'Ponte conectada':'Reconectando')+' <span style="color:#9f8cb4">✧</span></span></footer></div></section>';
}
function quick() {
  const name=profileName();
  return '<section class="quick-window" aria-label="Painel rápido"><header class="quick-top"><span class="quick-brand">laylay<span class="online-dot '+(state.connected?'':'offline')+'"></span></span><div class="quick-tools"><button class="icon-btn" data-mode="full" aria-label="Abrir interface completa">'+icon('expand')+'</button><button class="icon-btn" data-mode="island" aria-label="Recolher para ilha">'+icon('minus')+'</button></div></header><div class="quick-greeting">'+avatar('avatar-small')+'<div><h2>Estou por aqui'+(name?', '+escapeHTML(name):'')+'.</h2><p>'+status()+'</p></div></div><div class="quick-history" id="chat-history" tabindex="0" role="region" aria-label="Histórico da conversa">'+messages()+'</div><div class="quick-bottom">'+musicCard(true)+compose()+'<div class="simulation-bar"><span>'+escapeHTML(state.connected?'Ponte conectada':'Reconectando')+'</span>'+voiceSwitch()+'</div><button class="quick-expand" data-mode="full">Abrir meu espaço '+icon('arrow')+'</button></div></section>';
}
function fullWithMobileNavigation() {
  const label=state.mobileNavOpen?'Fechar navegação':'Abas';
  let markup=full().replace('<div class="breadcrumb">','<button class="pr-mobile-nav" data-action="toggle-navigation" aria-label="'+(state.mobileNavOpen?'Fechar navegação das abas':'Abrir navegação das abas')+'" aria-expanded="'+Boolean(state.mobileNavOpen)+'">'+icon('panel')+'<span>'+label+'</span></button><div class="breadcrumb">');
  markup=markup.replace('<button class="icon-btn" data-mode="quick"','<button class="icon-btn" data-mode="desktop" aria-label="Mostrar Laylay no desktop" title="Companhia no desktop">'+icon('island')+'</button><button class="icon-btn" data-mode="quick"');
  for(const [id,name]of pages)markup=markup.replace('data-page="'+id+'" ','data-page="'+id+'" aria-label="'+name+'" title="'+name+'" ');
  return markup;
}
function island() {
  return '<div class="island-wrap"><button class="island" data-mode="quick" aria-label="Laylay '+escapeHTML(connectionStatus().label)+'. Abrir painel rápido">'+avatar('avatar-mini')+'<span><strong>Laylay</strong><small>'+escapeHTML(connectionStatus().label)+'</small></span><span class="online-dot '+(state.connected?'':'offline')+'"></span></button></div>';
}
function fieldKey(el,index) {return el.id?'#'+el.id:el.getAttribute('data-field')?'field:'+el.getAttribute('data-field'):el.name?'name:'+el.name:'index:'+index;}
function desktop() {
  const recent=activeMessages().filter(m=>m.role==='assistant').at(-1);
  const pending=Object.values(state.pending).some(p=>p.kind==='texto'&&['sending','accepted','received','executing'].includes(p.state));
  const pageView=state.desktopView==='page';
  const view=views[state.page]||({home,chat}[state.page]);
  const content=pageView&&typeof view==='function'?view():'';
  const tabs=pages.map(([id,label])=>'<button data-page="'+id+'" class="'+(pageView&&state.page===id?'active':'')+'" '+(pageView&&state.page===id?'aria-current="page"':'')+'>'+icon(id)+'<span>'+label+'</span></button>').join('');
  const liveActivity=['idle','speaking','thinking','listening','executing','reconnecting'].includes(state.activity)?state.activity:'idle';
  const indicator=connectionStatus();
  return '<section class="desktop-island" aria-label="Laylay no desktop" data-desktop-state="'+state.desktopState+'" data-desktop-material="'+state.desktopMaterial+'" data-activity="'+liveActivity+'" data-desktop-view="'+(pageView?'page':'overview')+'">'+
    '<button class="desktop-compact" data-desktop-drag title="Arraste para mover. Clique para expandir." data-desktop="expandir" aria-label="Expandir Laylay · '+escapeHTML(indicator.label)+'"><span class="desktop-miniature">'+avatar('avatar-mini')+'</span><span class="desktop-compact-copy"><strong>Laylay</strong><small title="'+escapeHTML(indicator.detail)+'">'+escapeHTML(indicator.label)+'</small></span><span class="desktop-signal '+(indicator.kind==='online'?'online':indicator.kind)+'" aria-hidden="true"></span><span class="desktop-expand-icon">'+icon('chevron')+'</span></button>'+
    '<div class="desktop-expanded"><header class="desktop-toolbar window-head" data-desktop-drag title="Arraste esta área para mover a Laylay."><span class="desktop-wordmark wordmark">laylay<span>por perto</span></span><div class="desktop-toolbar-actions"><button class="desktop-overview-button icon-btn '+(!pageView?'active':'')+'" data-desktop="resumo" aria-label="Visão rápida" title="Visão rápida">'+icon('island')+'</button><span class="desktop-divider"></span>'+voiceSwitch()+'<button class="icon-btn" data-desktop="recolher" aria-label="Recolher Laylay" title="Recolher · Esc">'+icon('minus')+'</button></div></header>'+
    '<div class="desktop-window-body window-body"><nav class="desktop-tabs" aria-label="Abas da Laylay"><div class="nav-caption">SEU ESPAÇO</div>'+tabs+'<div class="nav-bottom">'+status()+'</div></nav>'+
    '<div class="desktop-overview"><div class="desktop-content"><section class="desktop-presence"><div class="desktop-portrait">'+avatar()+'</div><div class="desktop-presence-copy"><strong>Estou por aqui.</strong>'+status()+'</div></section><section class="desktop-context" aria-label="Sua trilha"><div class="desktop-section-label">SUA TRILHA<button data-page="music" aria-label="Ver biblioteca">'+icon('arrow')+'</button></div>'+musicCard(true)+'</section></div>'+
    '<div class="desktop-message" role="status"><span>'+icon(pending?'clock':'chat')+'</span><p>'+escapeHTML(pending?'Aguardando a Laylay…':recent?.text||'Uma conversa, uma ideia ou só companhia.')+'</p><button data-page="chat" aria-label="Ver conversa completa">'+icon('arrow')+'</button></div>'+
    '<div class="desktop-composer">'+(!pageView?compose():'')+'</div><footer class="desktop-foot"><span>'+escapeHTML(state.connected?'Ponte conectada':'Aguardando ponte')+'</span><span title="Ao mudar de aplicativo, Laylay recolhe, exceto durante a fala ou transmissão ativa. Esc recolhe manualmente.">Recolhe ao mudar de app</span></footer></div>'+
    '<div class="desktop-page main-column"><div class="context-bar"><span>Laylay <b>›</b> '+escapeHTML(pageLabel())+'</span><span class="context-state">'+status()+'</span></div><details class="desktop-conversations" '+(state.page==='chat'?'':'hidden')+'><summary>'+icon('chat')+' Suas conversas</summary>'+conversationList()+'</details><div class="desktop-page-content page" id="page-content" data-page="'+state.page+'" data-render-key="desktop-page:'+state.page+'">'+content+'</div><footer class="window-foot"><span>Seu espaço, no seu tempo.</span><span>'+escapeHTML(state.connected?'Conectada à Laylay':'Aguardando conexão')+'</span></footer></div></div></div></section>';
}
paths.pin='<path d="m9 3 6 0-1 5 4 4v2H6v-2l4-4-1-5ZM12 14v7"/>';
function desktopGesture(gesture){if(bridge&&typeof bridge.gesto_desktop==='function')bridge.gesto_desktop(gesture);}
function finishDesktopDrag(suppress=false){
  if(suppress)suppressDesktopClick=true;
  if(desktopDrag){try{desktopDrag.handle.releasePointerCapture(desktopDrag.id);}catch(_error){}}
  desktopDrag=null;document.body.classList.remove('desktop-dragging');
}
function startDesktopDrag(event){
  if(event.isTrusted)suppressDesktopClick=false;
  if(state.mode!=='desktop'||event.button!==0||event.pointerType!=='mouse'||!event.isTrusted)return;
  const handle=event.target.closest('[data-desktop-drag]');
  if(!handle)return;
  const control=event.target.closest('button,input,textarea,select,a,summary,[contenteditable=true]');
  if(control&&control!==handle)return;
  desktopDrag={id:event.pointerId,handle,x:event.clientX,y:event.clientY,active:false};
  try{handle.setPointerCapture(event.pointerId);}catch(_error){}
}
function moveDesktopDrag(event){
  if(!desktopDrag||event.pointerId!==desktopDrag.id)return;
  const dx=event.clientX-desktopDrag.x,dy=event.clientY-desktopDrag.y;
  if(!desktopDrag.active&&Math.hypot(dx,dy)>=6){
    desktopDrag.active=true;document.body.classList.add('desktop-dragging');
    if(bridge&&typeof bridge.arrastar_desktop==='function')bridge.arrastar_desktop(Math.round(dx),Math.round(dy));
  }
  if(desktopDrag.active)event.preventDefault();
}
function releaseDesktopDrag(event){
  if(!desktopDrag||event.pointerId!==desktopDrag.id)return;
  const active=desktopDrag.active;
  if(active){event.preventDefault();if(bridge&&typeof bridge.finalizar_arrasto_desktop==='function')bridge.finalizar_arrasto_desktop();}
  finishDesktopDrag(active);
}
function desktopEditing(){
  if(state.mode!=='desktop'||!bridge||typeof bridge.edicao_desktop!=='function')return;
  bridge.edicao_desktop(Boolean(state.draft||composing||document.activeElement?.matches('input,textarea,select')||document.querySelector('dialog[open]')));
}
function localDesktopActivity(event){
  if(state.mode==='desktop'&&state.desktopState==='expanded'&&event.isTrusted&&bridge&&typeof bridge.atividade_desktop==='function')bridge.atividade_desktop(event.type);
}
function queuePresentationCommit(){
  const active=state.mode==='desktop'&&['committing','starting'].includes(state.desktopPhase);
  if(!active){if(presentationAckFrame)cancelAnimationFrame(presentationAckFrame);presentationAckFrame=0;presentationAckKey='';return;}
  if(!bridge||typeof bridge.transicao_pronta!=='function')return;
  const key=state.desktopTransition+':'+state.desktopPhase;
  if(presentationAckKey===key)return;
  if(presentationAckFrame)cancelAnimationFrame(presentationAckFrame);
  presentationAckKey=key;
  const check=()=>{
    if(presentationAckKey!==key)return;
    if(window.innerWidth!==state.desktopTargetWidth||window.innerHeight!==state.desktopTargetHeight){presentationAckFrame=requestAnimationFrame(check);return;}
    presentationAckFrame=requestAnimationFrame(()=>{presentationAckFrame=requestAnimationFrame(()=>{
      presentationAckFrame=0;
      if(presentationAckKey===key)bridge.transicao_pronta(state.desktopTransition,window.innerWidth,window.innerHeight);
    });});
  };
  presentationAckFrame=requestAnimationFrame(check);
}
function queueStreamingViewport(){
  if(streamingViewportFrame)return;
  streamingViewportFrame=requestAnimationFrame(()=>{
    streamingViewportFrame=0;
    if(!bridge||typeof bridge.viewport_streaming!=='function'||!state.streamingOpen||state.page!=='streaming')return;
    const placeholder=document.getElementById('streaming-viewport'),page=document.getElementById('page-content');
    if(!placeholder||!page)return;
    const source=(state.streamingExpanded?page:placeholder).getBoundingClientRect(),clip=page.getBoundingClientRect();
    const x=Math.max(0,source.left,clip.left),y=Math.max(0,source.top,clip.top),right=Math.min(window.innerWidth,source.right,clip.right),bottom=Math.min(window.innerHeight,source.bottom,clip.bottom);
    bridge.viewport_streaming(JSON.stringify({x,y,width:Math.max(0,right-x),height:Math.max(0,bottom-y)}));
  });
}
function observeStreamingViewport(){
  const element=state.streamingOpen&&state.page==='streaming'?document.getElementById('streaming-viewport'):null;
  if(element!==streamingViewportElement){
    streamingViewportObserver?.disconnect();streamingViewportElement=element;
    if(element){streamingViewportObserver=new ResizeObserver(queueStreamingViewport);streamingViewportObserver.observe(element);element.scrollIntoView({block:'start',inline:'nearest'});}
  }
  if(element)queueStreamingViewport();
}
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
  const saved=savePresentation(),location=presentationLocation();
  document.body.classList.toggle('reduced',state.preferences.reduced);
  document.body.classList.toggle('cyan',state.preferences.accent==='cyan');
  document.body.classList.toggle('tp-hide-mascot',!state.preferences.mascot);
  document.body.classList.toggle('tp-sidebar-compact',!state.preferences.sidebar);
  document.body.classList.toggle('pr-nav-open',Boolean(state.mobileNavOpen));
  document.body.classList.toggle('native-quick-desktop',state.mode==='quick'&&state.nativeWindow&&state.availableWidth>=425&&state.availableHeight>=720);
  for(const mode of ['full','quick','island','desktop'])document.body.classList.toggle('mode-'+mode,state.mode===mode);
  document.documentElement.classList.toggle('desktop-transparent',state.mode==='desktop');
  document.body.classList.toggle('desktop-transitioning',state.mode==='desktop'&&state.desktopPhase!=='idle');
  document.body.classList.add('refined-ui');
  document.body.classList.toggle('desktop-entering',state.mode==='desktop'&&state.desktopEntry===true&&!state.preferences.reduced);
  const template=document.createElement('template');
  const projection=state.mode==='full'?fullWithMobileNavigation():state.mode==='quick'?quick():state.mode==='desktop'?desktop():island();
  template.innerHTML=projection;
  if(location!==previousLocation&&previousLocation)locationScroll.set(previousLocation,saved.scroll);
  if(location===previousLocation||(state.mode==='desktop'&&previousLocation.startsWith('desktop:')))reconcileChildren(root,template.content);
  else root.replaceChildren(template.content);
  restorePresentation(saved,location===previousLocation);
  if(location!==previousLocation) {
    for(const entry of locationScroll.get(location)||[]) {
      const node=entry.key.startsWith('.')?root.querySelector(entry.key):document.getElementById(entry.key);
      if(node)node.scrollTop=entry.top;
    }
    if(state.mode!=='desktop')document.getElementById('page-content')?.animate([{opacity:.55,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:state.preferences.reduced||window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:180,easing:'ease-out'});
    if(state.page==='chat'&&!locationScroll.has(location))scrollChat();
  }
  document.title='Laylay · '+(state.mode==='quick'?'Painel rápido':state.mode==='island'?'Ilha':pageLabel());
  if(location!==previousLocation)document.querySelector(state.mode==='desktop'?'.desktop-tabs [aria-current="page"]':'.nav [aria-current="page"]')?.scrollIntoView({block:'nearest',inline:'nearest'});
  previousLocation=location;
  animateDesktopMotion(location);
  avatarMotion.refresh();
  desktopEditing();
  queuePresentationCommit();
  observeStreamingViewport();
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
  if(!['full','quick','island','desktop'].includes(mode))return;
  state.mode=mode;
  if(bridge&&typeof bridge.apresentar==='function')bridge.apresentar(mode);
  render();
  if(mode==='quick')scrollChat();
}
function goPage(page) {
  const normalized=Object.keys(nativePages).find(key=>key===page||nativePages[key]===page);
  if(!normalized)return;
  state.page=normalized;state.mobileNavOpen=false;
  if(state.mode==='desktop'){
    state.desktopView='page';state.desktopState='expanded';
  }else{
    state.mode='full';
    if(bridge&&typeof bridge.apresentar==='function')bridge.apresentar('full');
  }
  request('pagina',{name:nativePages[normalized]});
  // No desktop, o owner nativo congela o quadro atual antes de publicar o
  // destino. A nova página só pinta atrás dessa cobertura, sem reflow visível.
  if(state.mode==='desktop'&&bridge&&typeof bridge.solicitar==='function')return;
  render();
  if(normalized==='chat'&&!locationScroll.has(presentationLocation()))scrollChat();
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
  if(data.emotion_level!==undefined&&Number.isFinite(Number(data.emotion_level)))assign('emotionLevel',Math.max(1,Math.min(3,Math.round(Number(data.emotion_level)||1))));
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
  // Cursor do SO é uma observação visual local: sem replay, render ou mente.
  if(type==='cursor_desktop'){avatarMotion.desktopPointer(msg);return;}
  if(type==='arrasto_desktop'){
    document.body.classList.toggle('desktop-dragging',msg.active===true);
    if(msg.active===false)finishDesktopDrag(Boolean(desktopDrag?.active));
    return;
  }
  let repaint=true;
  if(type==='snapshot')eventReplay.length=0;
  eventReplay.push(msg);if(eventReplay.length>200)eventReplay.shift();
  if(type==='apresentacao') {
    if(['full','quick','island','desktop'].includes(msg.mode))state.mode=msg.mode;
    if(['compact','expanded'].includes(msg.desktop_state))state.desktopState=msg.desktop_state;
    if(['acrylic','mica','fallback'].includes(msg.desktop_material))state.desktopMaterial=msg.desktop_material;
    if(['overview','page'].includes(msg.desktop_view))state.desktopView=msg.desktop_view;
    if(Object.hasOwn(nativePages,msg.desktop_page))state.page=msg.desktop_page;
    if(typeof msg.desktop_pinned==='boolean')state.desktopPinned=msg.desktop_pinned;
    if(['idle','resizing','committing','starting'].includes(msg.desktop_phase))state.desktopPhase=msg.desktop_phase;
    if(Number.isFinite(msg.desktop_transition))state.desktopTransition=msg.desktop_transition;
    if(Number.isFinite(msg.desktop_target_width))state.desktopTargetWidth=msg.desktop_target_width;
    if(Number.isFinite(msg.desktop_target_height))state.desktopTargetHeight=msg.desktop_target_height;
    if(typeof msg.streaming_open==='boolean')state.streamingOpen=msg.streaming_open;
    if(typeof msg.streaming_expanded==='boolean')state.streamingExpanded=msg.streaming_expanded;
    if(typeof msg.desktop_entry==='boolean')state.desktopEntry=msg.desktop_entry;
    if(typeof msg.visible==='boolean')state.windowVisible=msg.visible;
    if(typeof msg.native_window==='boolean')state.nativeWindow=msg.native_window;
    if(Number.isFinite(msg.available_width))state.availableWidth=msg.available_width;
    if(Number.isFinite(msg.available_height))state.availableHeight=msg.available_height;
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
      state.emotion='neutra';state.emotionLevel=1;
      for(const [key,p] of Object.entries(state.pending))if(['sending','accepted','received','executing'].includes(p.state))failPending(key,'Conexão interrompida antes da conclusão.');
    }
  } else if(type==='preferencias_ui') {
    const pref=object(msg.preferences||msg);
    for(const key of ['reduced','mascot','sidebar','desktop_start'])if(typeof pref[key]==='boolean')state.preferences[key]=pref[key];
    if(['violet','cyan'].includes(pref.accent))state.preferences.accent=pref.accent;
    if(typeof pref.profile_name==='string')state.preferences.profile_name=pref.profile_name;
    if(pref.home&&typeof pref.home==='object')state.preferences.home={version:1,period_days:pref.home.period_days===7?7:30,pinned_ids:list(pref.home.pinned_ids),hidden_ids:list(pref.home.hidden_ids)};
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
    if(msg.emotion_level!==undefined&&Number.isFinite(Number(msg.emotion_level)))state.emotionLevel=Math.max(1,Math.min(3,Math.round(Number(msg.emotion_level)||1)));
  } else if(type==='state') {
    repaint=applyState(msg)||!!msg.event;
    if(msg.event)state.events.push(msg.event);
  } else if(type==='dashboard_state') {
    if(msg.dashboard&&typeof msg.dashboard==='object')state.dashboard=msg.dashboard;
  } else if(type==='conversations_state') {
    if(msg.conversations)setConversationSnapshot(msg.conversations,msg.success===true&&['create','select','delete','list'].includes(msg.action));
    if(id)(state.pending[id]||(state.pending[id]={})).state=msg.success?'confirmed':'failed';
    if(msg.success&&['create','select','delete'].includes(msg.action))goPage('chat');
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
  if(type==='dev_events')repaint=['full','desktop'].includes(state.mode)&&state.page==='dev';
  if(type==='dashboard_state')repaint=state.mode==='quick'||(state.mode==='desktop'&&state.desktopView==='overview')||(['full','desktop'].includes(state.mode)&&state.page!=='chat');
  if(type==='dashboard_state'||type==='state')refreshStatusNodes();
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
  document.addEventListener('pointerdown',startDesktopDrag,{capture:true});
  document.addEventListener('pointermove',moveDesktopDrag,{capture:true,passive:false});
  document.addEventListener('pointerup',releaseDesktopDrag,{capture:true});
  document.addEventListener('pointercancel',()=>{if(desktopDrag&&!desktopDrag.active)finishDesktopDrag();},{capture:true});
  document.addEventListener('click',event=>{if(suppressDesktopClick){suppressDesktopClick=false;event.preventDefault();event.stopImmediatePropagation();}},{capture:true});
  document.addEventListener('submit',event=>{
    if(!event.target.matches('[data-composer]'))return;
    event.preventDefault();sendMessage();
  });
  document.addEventListener('input',event=>{
    if(event.target.matches('#composer-input'))state.draft=event.target.value;
    desktopEditing();
  });
  document.addEventListener('compositionstart',()=>{composing=true;desktopEditing();bridge?.composicao_desktop?.(true);});
  document.addEventListener('compositionend',()=>{composing=false;scheduleRender();desktopEditing();bridge?.composicao_desktop?.(false);});
  for(const type of ['pointerdown','wheel','keydown','input','compositionstart','compositionend'])document.addEventListener(type,localDesktopActivity,{passive:true});
  document.addEventListener('focusin',desktopEditing);
  document.addEventListener('focusout',()=>setTimeout(desktopEditing,0));
  document.addEventListener('pointerdown',()=>{if(state.mode==='desktop'&&state.desktopState==='expanded')desktopGesture('interagir');},{passive:true});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&state.streamingExpanded){event.preventDefault();desktopGesture('streaming-voltar');return;}
    if(event.key==='Escape'&&state.mode==='desktop'&&!composing&&!document.querySelector('dialog[open]')){event.preventDefault();desktopGesture('recolher');return;}
    if(event.key==='Escape'&&state.mobileNavOpen){state.mobileNavOpen=false;render();document.querySelector('.pr-mobile-nav')?.focus();}
  });
  document.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button||button.disabled)return;
    if(button.hasAttribute('data-home-period')){changeHomePreference('period_days',Number(button.dataset.homePeriod)===7?7:30);return;}
    if(button.hasAttribute('data-home-pin')){const id=button.dataset.homePin,values=homePreferences().pinned_ids;changeHomePreference('pinned_ids',values.includes(id)?values.filter(value=>value!==id):values.concat(id).slice(-32));return;}
    if(button.hasAttribute('data-home-hide')){const id=button.dataset.homeHide,values=homePreferences().hidden_ids;changeHomePreference('hidden_ids',Array.from(new Set(values.concat(id))).slice(-32));return;}
    if(button.hasAttribute('data-home-restore')){changeHomePreference('hidden_ids',[]);return;}
    if(button.hasAttribute('data-home-why')){confirmDialog('Por que apareceu?',button.dataset.reason||'Este atalho foi escolhido a partir do uso confirmado no período.',null,{label:'Entendi'});return;}
    if(button.hasAttribute('data-home-execute')){const id=button.dataset.homeExecute.slice(7),action=homeAction(id);if(action?.available){if(action.page)goPage(action.page);else request('acao',{action:id,request:action.request,payload:{}});}return;}
    if(button.dataset.desktop){desktopGesture(button.dataset.desktop);return;}
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
    if(action==='toggle-navigation'){state.mobileNavOpen=!state.mobileNavOpen;render();if(state.mobileNavOpen)document.querySelector('.sidebar .nav [aria-current="page"]')?.focus({preventScroll:true});return;}
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
  if(presentationAckFrame)cancelAnimationFrame(presentationAckFrame);
  if(streamingViewportFrame)cancelAnimationFrame(streamingViewportFrame);
  streamingViewportObserver?.disconnect();
},{once:true});
window.addEventListener('resize',queueStreamingViewport,{passive:true});
document.addEventListener('scroll',queueStreamingViewport,{passive:true,capture:true});
paths.mic='<path d="M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0ZM5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>';
paths.more='<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>';
window.LaylayInterface={state,icon,escapeHTML,pageHeading,avatar,status,compose,musicCard,render,invalidate:scheduleRender,goPage,goMode,toast,request,views,onEvent,receiveEvent,confirm:confirmDialog,safeArtwork,motionStats:()=>({count:motionRunCount,location:motionLocation,desktopState:motionDesktopState})};
const avatarMotion=(()=>{
 const reducedQuery=window.matchMedia('(prefers-reduced-motion: reduce)');
 let avatars=[],frame=0,blinkTimer=0,lastFrame=0,targetsDirty=true,pointer=null,environment='';
 let focused=document.hasFocus();
 const canAnimate=()=>!state.preferences.reduced&&!reducedQuery.matches&&!document.hidden&&(focused||state.mode==='desktop')&&state.windowVisible;
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
   if(!pointer){avatar.tx=avatar.ty=0;continue}
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
  document.body.classList.toggle('avatar-motion-paused',document.hidden||(!focused&&state.mode!=='desktop')||!state.windowVisible);
  const nextEnvironment=[reduced,document.hidden,focused,state.windowVisible,state.mode].join(':');
  if(environment===nextEnvironment&&elements.length===avatars.length&&elements.every((el,i)=>el===avatars[i].el))return;
  stop();environment=nextEnvironment;
  const existing=new Map(avatars.map(avatar=>[avatar.el,avatar]));
  avatars=elements.map(el=>existing.get(el)||({el,x:0,y:0,tx:0,ty:0}));
  neutralize();targetsDirty=true;
  if(!canAnimate()){pointer=null;return}
  if(pointer)requestTick();
  scheduleBlink(1500+Math.random()*1300);
 }
 window.addEventListener('pointermove',event=>{
  if(focused!==document.hasFocus())refresh();
  // O evento identifica o mouse real; WebViews podem informar hover:none mesmo com mouse.
  if(event.pointerType!=='mouse'||!canAnimate())return;
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
 function desktopPointer(data){
  if(state.mode!=='desktop'||!Number.isFinite(data.x)||!Number.isFinite(data.y))return;
  if(!canAnimate())return;
  pointer={x:data.x,y:data.y};targetsDirty=true;requestTick();
 }
 return {refresh,stop,desktopPointer};
})();

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();

