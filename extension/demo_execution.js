// Explicit, manual DEMO execution test. No automatic strategy or real orders.
(()=>{
const visible=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=="hidden";
const first=s=>[...document.querySelectorAll(s)].find(visible);
const text=e=>(e?.textContent||"").trim();
const demo=()=>{const s=text(first(".fund-pill"));return /\bdemo\b/i.test(s)&&!/\b(real|live)\b/i.test(s)};
const rows=()=>[...document.querySelectorAll("#pane-1 .el-table__body tbody tr.el-table__row")].filter(visible);
const id=r=>text(r.querySelectorAll("td")[10]);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
let busy=false,uncertain=false;
async function execute(side){
 if(busy||uncertain||!demo())throw Error("DEMO required; busy or unresolved order");
 busy=true;
 try{
 if(side==="CLOSE"){
 const list=rows();if(list.length!==1)throw Error("Exactly one visible position required");
 const r=list[0],key=id(r),button=r.querySelector("svg.operate");
 if(!key||!visible(button)||!demo())throw Error("Close control unavailable");
 if(!confirm("Close DEMO position "+key+"?"))return;
 uncertain=true;button.dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));
 }else{
 if(rows().length)throw Error("Existing position; close first");
 const market=first(".quotes #tab-first");if(!market)throw Error("Market tab missing");market.click();await wait(150);
 const tab=[...document.querySelectorAll("#sellBuy .el-segmented__item,.order-centent .el-segmented__item")].filter(visible).find(e=>(side==="BUY"?["beli","buy"]:["jual","sell"]).includes(text(e.querySelector(".el-segmented__item-label p:first-child")).toLowerCase()));
 if(!tab)throw Error("Direction missing");tab.click();await wait(200);
 if(!tab.classList.contains("is-selected")&&!tab.querySelector("input:checked"))throw Error("Direction not verified");
 const input=first('.order-centent input[min="0.01"]');if(!input)throw Error("Lot input missing");
 Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(input,"0.01");
 for(const name of ["input","change","blur"])input.dispatchEvent(new Event(name,{bubbles:true}));await wait(150);
 const b=first(".order-centent .fixed-btn-box button.quotes-logos,.order-centent .fixed-btn-box button.trade");
 if(!demo()||Number(input.value)!==0.01||!b||b.disabled||!(side==="BUY"?/beli|buy/i:/jual|sell/i).test(text(b)))throw Error("Order checks failed");
 if(!confirm("Submit DEMO "+side+" 0.01 lot?"))return;
 if(!demo()||rows().length)throw Error("Account or positions changed");
 uncertain=true;b.click();
 }
 alert("Request clicked. Confirm any broker dialog manually and verify position/history. Reload only after reconciliation.");
 }finally{busy=false}
}
const panel=document.createElement("div");panel.style.cssText="position:fixed;bottom:12px;right:12px;z-index:2147483647;background:#20242a;color:white;padding:8px;border-radius:8px;font:12px sans-serif";panel.textContent="DEMO execution test ";
for(const side of ["BUY","SELL","CLOSE"]){const b=document.createElement("button");b.textContent=side;b.style.margin="4px";b.onclick=()=>execute(side).catch(e=>alert(e.message));panel.append(b)}
document.body.append(panel);setInterval(()=>{panel.hidden=!demo()},500);panel.hidden=!demo();
})();