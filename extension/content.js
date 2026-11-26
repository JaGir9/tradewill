// Read-only: no cookies, tokens, password values, account IDs or orders.
function visible(e){return !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden";}
function first(s){return [...document.querySelectorAll(s)].find(visible);}
function txt(e){return (e?.innerText||"").trim();}
function observe(){
 const pill=first(".fund-pill");
 const marker=first(".fund-login");
 const balanceEl=first(".right-money-txt p,.right-money-txt");
 const raw=txt(pill);
 const hint=(raw.match(/\b(?:demo|real|live|cent|standard|usd|usc|akun)\b/gi)||[]).join(" ").slice(0,80);
 const b=txt(balanceEl);
 const balance=/^[\s$¢+\-\d.,]+$/.test(b)?b.slice(0,80):"";
 const trading=!!first("#sellBuy,.order-centent,.quotes-fx");
 const login=!!first('input[type="password"]');
 chrome.runtime.sendMessage({kind:"heartbeat",account_hint:hint,balance_text:balance,account_visible:!!(hint&&balance),account_marker:!!(pill||marker),trading_ui:trading,login_form:login,domain:location.hostname}).catch(()=>{});
}
observe();setInterval(observe,3000);
