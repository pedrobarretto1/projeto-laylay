'use strict';
const http=require('node:http'),fs=require('node:fs'),crypto=require('node:crypto'),{promisify}=require('node:util'),{Pool}=require('pg');
const pool=new Pool({connectionString:process.env.DATABASE_URL,max:4,connectionTimeoutMillis:8000});
const scrypt=promisify(crypto.scrypt), now=()=>Date.now(), hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const live=new Map(),limits=new Map();
const html=fs.readFileSync(__dirname+'/index.html');
const validKey=k=>typeof k==='string'&&/^[!-~]{16,18}$/.test(k)&&!k.includes('|');
const username=s=>typeof s==='string'&&/^[a-z0-9_.-]{3,32}$/.test(s);
const password=s=>typeof s==='string'&&s.length>=10&&s.length<=100;
function reply(res,code,data='',type='text/plain; charset=utf-8',extra={}){if(res.destroyed||res.writableEnded)return;const b=typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data);res.writeHead(code,{'Content-Type':type,'Content-Length':Buffer.byteLength(b),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',...extra});res.end(b);}
const json=(r,c,d)=>reply(r,c,d,'application/json; charset=utf-8');
function body(req){return new Promise((ok,bad)=>{let b='';req.setEncoding('utf8');req.on('data',x=>{b+=x;if(b.length>2048){bad(Error('large'));req.destroy()}});req.on('end',()=>ok(b));req.on('error',bad)})}
function cookie(req){return (req.headers.cookie||'').match(/(?:^|;\s*)lh_session=([a-f0-9]{64})(?:;|$)/)?.[1]||'';}
async function account(req){let c=cookie(req);if(!c)return null;const r=await pool.query('select username from lh_sessions where token=$1 and expires>now()',[hash(c)]);return r.rows[0]?.username||null;}
async function verify(u,p){if(!username(u)||!password(p))return false;const r=await pool.query('select salt,pass from lh_accounts where username=$1',[u]);const row=r.rows[0];const out=await scrypt(p,row?.salt||'00000000000000000000000000000000',32);return !!row&&crypto.timingSafeEqual(out,Buffer.from(row.pass,'hex'));}
function limited(req,kind,max){let ip=String(req.headers['x-forwarded-for']||req.socket.remoteAddress).split(',').pop().trim();let k=kind+':'+ip,t=now();let a=limits.get(k);if(!a||t-a.t>60000){a={t,n:0};if(limits.size>10000)return true;limits.set(k,a);}return ++a.n>max;}
function finish(d,c,b){let p=d.pending;if(!p)return;d.pending=null;clearTimeout(p.timer);reply(p.res,c,b);}
const server=http.createServer(async(req,res)=>{try{
 const path=new URL(req.url,'http://localhost').pathname;
 if(req.method==='GET'&&path==='/')return reply(res,200,html,'text/html; charset=utf-8');
 if(req.method==='GET'&&path==='/health')return reply(res,200,'ok');
 if(req.headers.origin&&req.headers.origin!=='https://'+req.headers.host&&req.headers.origin!=='http://'+req.headers.host)return reply(res,403,'origin');
 if(req.method==='GET'&&path==='/api/account/devices'){
 const u=await account(req);if(!u)return json(res,401,{error:'Entre na sua conta'});
 const r=await pool.query('select device_key,name from lh_devices where owner=$1 order by name',[u]);
 return json(res,200,{username:u,devices:r.rows.map(x=>({id:x.device_key,name:x.name,online:!!live.get(hash(x.device_key))&&now()-live.get(hash(x.device_key)).seen<20000}))});
 }
 if(req.method!=='POST')return reply(res,404,'not found');
 if(['/api/account/register','/api/account/login','/api/account/enroll'].includes(path)){
 if(limited(req,'auth',8))return reply(res,429,'Muitas tentativas. Aguarde um minuto.');
 const b=JSON.parse(await body(req)),u=String(b.username||'').trim().toLowerCase(),p=b.password;
 if(!username(u)||!password(p))return reply(res,400,'Usuario: 3 a 32 letras/numeros. Senha: 10 a 100 caracteres.');
 if(path.endsWith('/register')){
 const salt=crypto.randomBytes(16).toString('hex'),pass=(await scrypt(p,salt,32)).toString('hex');
 const r=await pool.query('insert into lh_accounts(username,salt,pass) values($1,$2,$3) on conflict do nothing returning username',[u,salt,pass]);if(!r.rowCount)return reply(res,409,'Usuario indisponivel.');
 }else if(!await verify(u,p))return reply(res,401,'Usuario ou senha incorretos.');
 if(path.endsWith('/enroll')){
 const key=req.headers['x-laylay-key'],name=b.name;
 if(!validKey(key)||typeof name!=='string'||name.length<1||name.length>20)return reply(res,400,'Dispositivo invalido.');
 const r=await pool.query('insert into lh_devices(device_key,owner,name) values($1,$2,$3) on conflict(device_key) do update set name=excluded.name where lh_devices.owner=excluded.owner returning device_key',[key,u,name]);if(!r.rowCount)return reply(res,409,'Dispositivo ja pertence a outra conta.');
 return reply(res,200,'OK');
 }
 const t=crypto.randomBytes(32).toString('hex');await pool.query("insert into lh_sessions(token,username,expires) values($1,$2,now()+interval '30 days')",[hash(t),u]);
 return reply(res,200,'OK','text/plain; charset=utf-8',{'Set-Cookie':'lh_session='+t+'; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000'});
 }
 if(path==='/api/account/logout'){const c=cookie(req);if(c)await pool.query('delete from lh_sessions where token=$1',[hash(c)]);return reply(res,200,'OK','text/plain; charset=utf-8',{'Set-Cookie':'lh_session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0'});}
 if(!['/api/device','/api/ack','/api/rele'].includes(path))return reply(res,404,'not found');
 if(limited(req,'iot',300))return reply(res,429,'rate limit');
 const key=req.headers['x-laylay-key'];if(!validKey(key))return reply(res,401,'invalid device');
 const b=await body(req),id=hash(key);let d=live.get(id);
 if(path==='/api/device'){
 if(!/^[01]$/.test(b))return reply(res,400,'state');
 if(!d){const r=await pool.query('select 1 from lh_devices where device_key=$1',[key]);if(!r.rowCount)return reply(res,401,'device not enrolled');if(live.size>=256)return reply(res,503,'capacity');d={seen:0,state:null,pending:null};live.set(id,d);}
 d.seen=now();d.state=b;const p=d.pending;
 if(p&&!p.delivered&&now()<p.expires){p.delivered=true;return reply(res,200,p.id+'|'+p.action);}return reply(res,200,'');
 }
 if(!d||now()-d.seen>20000)return reply(res,503,'ESP32 offline');
 if(path==='/api/ack'){const p=d.pending;if(!p||!p.delivered||b!==p.id+'|'+p.action||now()>=p.expires)return reply(res,409,'expired');d.state=p.action;d.seen=now();finish(d,200,d.state);return reply(res,200,'ok');}
 const u=await account(req);if(!u)return reply(res,401,'Entre na sua conta');
 const owned=await pool.query('select 1 from lh_devices where device_key=$1 and owner=$2',[key,u]);if(!owned.rowCount)return reply(res,403,'Dispositivo de outra conta');
 if(b==='S')return reply(res,200,d.state);if(!/^[01]$/.test(b))return reply(res,400,'action');if(d.pending)return reply(res,409,'busy');
 const p={id:crypto.randomBytes(12).toString('hex'),action:b,expires:now()+6500,delivered:false,res,timer:null};d.pending=p;p.timer=setTimeout(()=>finish(d,504,'sem confirmacao'),6500);
 res.on('close',()=>{if(d.pending===p){clearTimeout(p.timer);d.pending=null;}});
 }catch(e){reply(res,503,'Servico temporariamente indisponivel');}});
setInterval(()=>{for(const [k,d] of live)if(now()-d.seen>60000&&!d.pending)live.delete(k);for(const [k,v] of limits)if(now()-v.t>60000)limits.delete(k)},30000).unref();
server.requestTimeout=15000;server.headersTimeout=5000;server.listen(Number(process.env.PORT||10000),'0.0.0.0');
