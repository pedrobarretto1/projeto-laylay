// Demonstração isolada: reutiliza p.avatar e mascote.css oficiais, sem ponte.
(() => {
'use strict';
const p=window.LaylayInterface;
const emotions=[['calma','Neutra'],['alegre','Feliz'],['animada','Animada'],['curiosa','Curiosa'],['confusa','Confusa'],['triste','Triste'],['irritada','Brava'],['surpresa','Surpresa'],['envergonhada','Envergonhada']];
let emotion='calma',blinkTimer=0;
Object.assign(p.state,{connected:true,activity:'idle',emotionLevel:2});
function markup(name,size='') {const before=p.state.emotion;p.state.emotion=name;const result=p.avatar(size);p.state.emotion=before;return result;}
document.getElementById('expressions').innerHTML=emotions.map(([name,label])=>'<div class="expression">'+markup(name)+'<small>'+label+'</small></div>').join('');
const controls=document.getElementById('emotion-controls');
controls.innerHTML=emotions.map(([name,label])=>'<button data-demo-emotion="'+name+'" aria-pressed="'+(name===emotion)+'">'+label+'</button>').join('');
function present(){
 p.state.emotion=emotion;
 document.getElementById('portrait').innerHTML=p.avatar();
 document.getElementById('expression-title').textContent=emotions.find(([key])=>key===emotion)[1];
 document.querySelectorAll('[data-demo-emotion]').forEach(el=>el.setAttribute('aria-pressed',el.dataset.demoEmotion===emotion));
 document.getElementById('size-home').innerHTML=markup(emotion,'avatar-small');
 document.getElementById('size-panel').innerHTML=markup(emotion,'avatar-small');
 document.getElementById('size-chat').innerHTML=markup(emotion,'avatar-mini');
 document.getElementById('size-island').innerHTML=markup(emotion,'avatar-mini');
 p.render();
}
controls.addEventListener('click',event=>{const el=event.target.closest('[data-demo-emotion]');if(el){emotion=el.dataset.demoEmotion;present();}});
document.getElementById('level').addEventListener('input',event=>{p.state.emotionLevel=Number(event.target.value);document.getElementById('level-value').value=p.state.emotionLevel;document.querySelectorAll('.avatar').forEach(el=>el.dataset.emotionLevel=p.state.emotionLevel);});
document.getElementById('activity').addEventListener('change',event=>{p.state.activity=event.target.value;present();});
document.getElementById('reduce').addEventListener('click',event=>{p.state.preferences.reduced=!p.state.preferences.reduced;event.currentTarget.setAttribute('aria-pressed',p.state.preferences.reduced);p.render();});
document.getElementById('accent').addEventListener('click',event=>{p.state.preferences.accent=p.state.preferences.accent==='cyan'?'violet':'cyan';event.currentTarget.setAttribute('aria-pressed',p.state.preferences.accent==='cyan');p.render();});
document.getElementById('blink').addEventListener('click',()=>{clearTimeout(blinkTimer);document.querySelectorAll('.avatar').forEach(el=>el.classList.add('is-blinking'));blinkTimer=setTimeout(()=>document.querySelectorAll('.avatar').forEach(el=>el.classList.remove('is-blinking')),130);});
present();
})();
