// Fixture visual isolada: nenhum evento é enviado à Laylay.
(async () => {
  const ui=LaylayInterface;
  ui.request=async()=>'';
  const paint=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  ui.receiveEvent({type:'conexao',connected:true});
  ui.receiveEvent({type:'snapshot',state:{activity:'idle',activity_label:'Pronta',interaction_mode:'chat'},
    messages:[{id:'estudo',role:'assistant',text:'Texto de exemplo para avaliar a leitura de mensagens longas. '.repeat(12)}]});
  ui.goPage('chat');await paint();
  const bubble=document.querySelector('.bubble'), b=getComputedStyle(bubble);
  const report={origem:'fixture visual local sem executor',bubble:{font:b.fontSize,lineHeight:b.lineHeight,width:bubble.getBoundingClientRect().width}};
  ui.goPage('system');await paint();
  const page=document.getElementById('page-content');page.scrollTop=500;
  report.scrollBefore=page.scrollTop;
  ui.goPage('memory');await paint();ui.goPage('system');await paint();
  report.scrollAfter=page.scrollTop;
  report.scrollAfter=document.getElementById('page-content').scrollTop;
  ui.goPage('settings');await paint();
  report.settingsSections=[...document.querySelectorAll('.tp-section h3')].map(el=>({name:el.textContent,y:Math.round(el.getBoundingClientRect().y)}));
  ui.receiveEvent({type:'preferencias_ui',accent:'cyan'});
  await paint();
  report.cyan={token:getComputedStyle(document.body).getPropertyValue('--accent').trim(),
    activeNav:getComputedStyle(document.querySelector('.nav .active')).color,
    settingsPrimary:getComputedStyle(document.querySelector('[data-tp-action=settings-save]')).backgroundColor,
    settingsPrimaryBorder:getComputedStyle(document.querySelector('[data-tp-action=settings-save]')).borderColor};
  ui.receiveEvent({type:'preferencias_ui',accent:'violet'});ui.goPage('home');await paint();
  return JSON.stringify(report);
})()
