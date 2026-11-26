'use strict';
const $ = id => document.getElementById(id);
let lastAccount = null;
let accountChoicePending = false;
let configIsDirty = false;
const cfgForm = $('config');
const setMsg = (text, error=false) => { $('message').textContent = text; $('message').style.color = error?'#fca5a5':'#86efac'; };
async function req(url, body) {
  const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
  let data = await res.json();
  if(!res.ok) throw new Error(data.detail||`HTTP ${res.status}`);
  return data;
}
function loadConfig(c){
  for (const [k,v] of Object.entries(c)) {
    const e=cfgForm.elements.namedItem(k);if(!e)continue;
    if(e.type==='checkbox')e.checked=!!v;else e.value=String(v);
  }
  configIsDirty=false;
}
function encodeConfig(){
  let out={};for(const k of ['symbol','mode','lot_mode','direction'])out[k]=cfgForm.elements.namedItem(k).value;
  for(const k of ['manual_lot','risk_pct','daily_loss_pct'])out[k]=Number(cfgForm.elements.namedItem(k).value);
  for(const k of ['max_positions','min_score'])out[k]=Number(cfgForm.elements.namedItem(k).value);
  for(const k of ['pullback','breakout','trailing'])out[k]=cfgForm.elements.namedItem(k).checked;
  return out;
}
function td(val){const e=document.createElement('td');e.textContent=String(val??'—');return e;}
function tableRows(id,arr,fn){const body=$(id);body.replaceChildren();for(const item of arr){const tr=document.createElement('tr');for(const value of fn(item))tr.appendChild(td(value));body.appendChild(tr);}}
function render(s){
  $('status').textContent=s.status;
  $('acctLabel').textContent=s.account.toUpperCase();$('balance').textContent=s.balance===null?'NOT CONNECTED':'$'+s.balance.toFixed(2);
  $('equity').textContent=s.equity===null?'NOT CONNECTED':'$'+s.equity.toFixed(2);
  $('pnl').textContent='$'+s.metrics.realized_net.toFixed(2);
  $('winrate').textContent=s.metrics.win_rate===null?'—':s.metrics.win_rate+'%';
  $('open').textContent=s.positions.length;
  $('price').textContent=s.price??'—';$('feedStatus').textContent=s.market_source+' | feed ready: '+s.feed_ready;$('saveBalance').disabled=s.account!=='simulation'||s.status!=='STOPPED';$('signal').textContent=s.signal.side;$('strategy').textContent=s.signal.strategy;$('score').textContent=s.signal.score+'/100';$('reason').textContent=s.signal.reason;
  $('broker').textContent='Broker orders: DISABLED';
  $('switch').disabled=s.status!=='STOPPED';
  for(const b of document.querySelectorAll('[data-action]')){const a=b.dataset.action;b.disabled=(a==='start'&&(s.status==='RUNNING'||(s.account!=='demo'&&(s.account!=='simulation'||!s.feed_ready))))||(a==='pause'&&s.status!=='RUNNING');}
  if(!accountChoicePending) $('account').value=s.account;
  if(lastAccount!==s.account){lastAccount=s.account;loadConfig(s.config);}
  if(!configIsDirty && s.status==='STOPPED')loadConfig(s.config);
  for(const el of cfgForm.querySelectorAll('input,select,button'))el.disabled=s.status!=='STOPPED';
  tableRows('positions',s.positions,p=>[p.id,p.symbol,p.side,p.lot,p.entry.toFixed(4),p.stop.toFixed(4),p.target.toFixed(4),p.net.toFixed(3)]);
  tableRows('history',s.history,t=>[t.closed_at,t.symbol,t.side,t.lot,t.strategy,t.net.toFixed(3),t.reason]);
  $('events').textContent=s.events.map(e=>`${e.ts}: ${e.event}`).join('\n');
}
async function refresh(){try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error('Cannot load state');render(await r.json());}catch(e){setMsg('Backend disconnected: '+e.message,true);}}
$('account').addEventListener('change',()=>{accountChoicePending=true;});
$('switch').addEventListener('click',async()=>{
  const a=$('account').value;
  if(a!=='demo'&&a!=='simulation'&&!confirm('Akun REAL belum terhubung dan trading akan tetap terkunci. Pilih untuk menyimpan konfigurasi saja?')){accountChoicePending=false;await refresh();return;}
  try{await req('/api/account',{account:a});accountChoicePending=false;lastAccount=null;setMsg('Akun pilihan diperbarui. Bukan pergantian akun di website TradeWill.');await refresh();}catch(e){accountChoicePending=false;setMsg(e.message,true);await refresh();}
});
cfgForm.addEventListener('input',()=>{configIsDirty=true;});
cfgForm.addEventListener('submit',async e=>{e.preventDefault();try{await req('/api/config',{config:encodeConfig()});configIsDirty=false;setMsg('Konfigurasi tersimpan untuk akun terpilih.');await refresh();}catch(err){setMsg(err.message,true);}});
for(const b of document.querySelectorAll('[data-action]'))b.addEventListener('click',async()=>{
  const a=b.dataset.action;
  if(a==='emergency'&&!confirm('Tutup semua posisi PAPER milik bot dan stop entry?'))return;
  if(a==='start'&&!confirm('Jalankan strategi PAPER? Tidak mengirim order TradeWill.'))return;
  try{await req('/api/control/'+a);setMsg('Perintah '+a+' berhasil pada engine PAPER.');await refresh();}catch(e){setMsg(e.message,true);}
});
refresh();setInterval(refresh,1500);

$('saveBalance').addEventListener('click',async()=>{try{await req('/api/virtual-balance',{amount:Number($('virtualBalance').value)});await refresh();setMsg('Saldo virtual tersimpan');}catch(e){setMsg(e.message,true);}});


$('pairBridge').addEventListener('click',async()=>{try{const r=await fetch('/api/bridge/pair');if(!r.ok)throw Error('Pairing unavailable');const d=await r.json();await navigator.clipboard.writeText(d.key);setMsg('Paste key into extension options.');}catch(e){setMsg(e.message,true);}});
async function bridgeRefresh(){try{const r=await fetch('/api/bridge/status',{cache:'no-store'});const d=await r.json();$('loginStatus').textContent=d.fresh?'CONNECTED | '+d.connection+' | login UNVERIFIED':'DISCONNECTED / heartbeat stale';$('observedAccount').textContent=d.fresh?'Observed account: '+(d.observation.account_hint||'—')+' | observed balance: '+(d.observation.balance_text||'—')+' | domain: '+(d.observation.domain||'—'):'No fresh observation';}catch(e){$('loginStatus').textContent='Bridge unavailable';}}
bridgeRefresh();setInterval(bridgeRefresh,2000);
