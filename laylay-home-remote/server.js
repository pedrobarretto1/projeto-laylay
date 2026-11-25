'use strict';
const http=require('node:http'), fs=require('node:fs'), crypto=require('node:crypto');
const html=fs.readFileSync(__dirname+'/index.html');
const sessions=new Map(), hits=new Map();
const keyOK=k=>typeof k==='string'&&/^[!-~]{16,18}$/.test(k)&&!k.includes('|');
const digest=k=>crypto.createHash('sha256').update(k).digest('hex');
const now=()=>Date.now();
function reply(res,code,body=''){if(!res.destroyed&&!res.writableEnded){res.writeHead(code,{'Content-Type':'text/plain; charset=utf-8','Content-Length':Buffer.byteLength(body),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'});res.end(body);}}
function body(req){return new Promise((resolve,reject)=>{let b='';req.setEncoding('utf8');req.on('data',c=>{b+=c;if(b.length>128){reject(Error('large'));req.destroy()}});req.on('end',()=>resolve(b));req.on('error',reject);});}
function finish(d,code,v){const p=d.pending;if(!p)return;d.pending=null;clearTimeout(p.timer);reply(p.res,code,v);}
const server=http.createServer(async(req,res)=>{
 try{
 const url=new URL(req.url,'http://localhost').pathname;
 if(req.method==='GET'&&url==='/'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer'});return res.end(html);}
 if(req.method==='GET'&&url==='/health')return reply(res,200,'ok');
 if(req.method!=='POST'||!['/api/rele','/api/device','/api/ack'].includes(url))return reply(res,404,'not found');
 if(req.headers.origin && req.headers.origin!=='https://'+req.headers.host && req.headers.origin!=='http://'+req.headers.host)return reply(res,403,'origin');
 const key=req.headers['x-laylay-key'];if(!keyOK(key))return reply(res,401,'invalid key');
 const ip=String(req.headers['x-forwarded-for']||req.socket.remoteAddress||'').split(',')[0].trim();const t=now();let hit=hits.get(ip);if(!hit||t-hit.start>60000){hit={start:t,n:0};if(hits.size<2000||hits.has(ip))hits.set(ip,hit);}if(++hit.n>180)return reply(res,429,'rate limit');const b=await body(req),id=digest(key);let d=sessions.get(id);
 if(url==='/api/device'){
  if(!/^[01]$/.test(b))return reply(res,400,'state');
  if(!d){if(sessions.size>=256)return reply(res,503,'capacity');d={seen:0,state:null,pending:null};sessions.set(id,d);}
  d.seen=now();d.state=b;
  const p=d.pending;if(p&&!p.delivered&&now()<p.expires){p.delivered=true;return reply(res,200,p.id+'|'+p.action);}
  return reply(res,200,'');
 }
 if(!d||now()-d.seen>15000)return reply(res,503,'ESP32 offline');
 if(url==='/api/ack'){
  const p=d.pending;if(!p||!p.delivered||b!==p.id+'|'+p.action||now()>=p.expires)return reply(res,409,'expired or unmatched');
  d.state=p.action;d.seen=now();finish(d,200,d.state);return reply(res,200,'ok');
 }
 if(b==='S')return reply(res,200,d.state);
 if(!/^[01]$/.test(b))return reply(res,400,'action');
 if(d.pending)return reply(res,409,'busy');
 const p={id:crypto.randomBytes(12).toString('hex'),action:b,expires:now()+6500,delivered:false,res,timer:null};
 d.pending=p;p.timer=setTimeout(()=>finish(d,504,'no device confirmation'),6500);
 res.on('close',()=>{if(d.pending===p){clearTimeout(p.timer);d.pending=null;}});
 }catch(e){reply(res,400,'request failed');}
});
setInterval(()=>{for(const [id,d] of sessions)if(now()-d.seen>60000&&!d.pending)sessions.delete(id);for(const [ip,h] of hits)if(now()-h.start>60000)hits.delete(ip)},30000).unref();
server.requestTimeout=10000;server.headersTimeout=5000;server.maxHeadersCount=32;
server.listen(Number(process.env.PORT||10000),'0.0.0.0');
