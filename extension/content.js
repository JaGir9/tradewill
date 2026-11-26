// Read visible account labels only. Never read cookies, credentials or tokens.
function visible(sel){const e=document.querySelector(sel);return e&&e.getClientRects().length?e.innerText.trim():"";}
function observe(){
 const hint=visible(".fund-pill").replace(/[^a-zA-Z\s$¢]/g,"").slice(0,80);
 const balance=visible(".right-money-txt p").replace(/[^0-9.,$¢+\-\s]/g,"").slice(0,80);
 chrome.runtime.sendMessage({kind:"heartbeat",account_hint:hint,balance_text:balance,account_visible:!!(hint&&balance)}).catch(()=>{});
}
observe();setInterval(observe,3000);
