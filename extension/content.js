// Read-only: no cookies, tokens, password values, account IDs or orders.
function visible(e){return !!e && e.getClientRects().length>0 && getComputedStyle(e).visibility!=="hidden";}
function first(s){return [...document.querySelectorAll(s)].find(visible);}
function txt(e){return (e?.innerText||"").trim();}
function quote(side){
 const tabs=[...document.querySelectorAll("#sellBuy .el-segmented__item,.order-centent .el-segmented__item")].filter(visible);
 const t=tabs.find(e=>side.includes(txt(e.querySelector(".el-segmented__item-label p:first-child")).toLowerCase()));
 const raw=txt(t?.querySelector(".quote-price"));
 return /^\d[\d,]*(\.\d+)?$/.test(raw)?Number(raw.replace(/,/g,"")):null;
}
function inspect(){
 const bid=quote(["jual","sell"]),ask=quote(["beli","buy"]);
 const symbol=txt(first(".symbolName,.usdt-pro.isApp")).split(/\s+/)[0];
 const lot=first('.order-centent input[min="0.01"]');
 const submit=first(".order-centent .fixed-btn-box button.quotes-logos,.order-centent .fixed-btn-box button.trade");
 return {symbol:/^[A-Za-z0-9/_-]{1,32}$/.test(symbol)?symbol:"",bid,ask,lot_ready:!!lot,submit_ready:!!submit&&!submit.disabled,close_controls:[...document.querySelectorAll("#pane-1 .el-table__body tbody tr.el-table__row svg.operate")].filter(visible).length};
}
let lastSent=0,lastSnapshot="";
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
 const market=inspect(); const signature=JSON.stringify(market); const now=Date.now(); if(now-lastSent<250||(signature===lastSnapshot&&now-lastSent<3000))return; lastSent=now;lastSnapshot=signature;
 chrome.runtime.sendMessage({kind:"heartbeat",...market,account_hint:hint,balance_text:balance,account_visible:!!(hint&&balance),account_marker:!!(pill||marker),trading_ui:trading,login_form:login,domain:location.hostname}).catch(()=>{});
}
observe();setInterval(observe,100);
