# Automated demo strategy testing: safe preview

This build adds an opt-in **automatic strategy evaluator**, not an order sender.

## Why broker order automation is still blocked
Current TradeWill bridge reads DOM text, which does not authenticate the selected account. There is no broker-confirmed account ID, no broker-sourced historical closed M1 candles, no authoritative fill/position reconciliation, no durable order idempotency and no verified kill-switch close. Sending trades from these observations can accidentally trade a real account or duplicate orders. The existing `extension/demo_execution.js` remains manual and requires confirmation.

## Use
1. Install the `feature/demo-auto-strategy-testing` branch and start the local backend.
2. Install/reload the extension, pair it, open the TradeWill site and log in manually.
3. POST `{"enabled":true}` to `http://127.0.0.1:8000/api/demo-auto/control`.
4. GET `/api/demo-auto/status` for gate failures, signal evaluations, and audit events.
5. Disable with `{"enabled":false}`. No broker order is ever sent.

## Required next integration
- Documented authorized broker DEMO trading API, or verified and authorized UI automation path
- Authenticated DEMO account ID/type confirmation on every order, not a DOM keyword
- Genuine timestamped bid/ask and 210+ broker-closed M1 candles
- Broker contract size, lot steps, margin, stop-distance and spread checks
- Unique client order IDs, persistent write-ahead intent, acknowledgement, restart reconciliation
- Broker-owned open position snapshots and confirmed closes
- Stop-loss/take-profit on broker side and kill switch
- Automated sandbox acceptance tests and forward-test reporting

The endpoint is intentionally read-only with respect to broker funds. Synthetic/paper results are not broker demo results.
