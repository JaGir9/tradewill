chrome.runtime.onMessage.addListener((m,sender)=>{
 if(m.kind!=="heartbeat"||!sender.tab||!sender.url)return;
 const u=new URL(sender.url);
 if(u.protocol!=="https:"||!(u.hostname==="tradewill.id"||u.hostname.endsWith(".tradewill.id")))return;
 chrome.storage.local.get("key").then(({key})=>{
 if(!key)return;
 return fetch("http://127.0.0.1:8000/api/bridge/heartbeat",{method:"POST",headers:{"Content-Type":"application/json","X-Bridge-Key":key},body:JSON.stringify({account_hint:m.account_hint,balance_text:m.balance_text,account_visible:m.account_visible})});
 }).catch(()=>{});
});
