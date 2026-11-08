// GlobalJiema activation flow — Node.js 18+, zero dependencies.
// node receive_sms.mjs <service> <country>
import { randomBytes } from 'node:crypto';

const API = 'https://globaljiema.com';
const KEY = process.env.GLOBALJIEMA_API_KEY;
if (!KEY) throw new Error('GLOBALJIEMA_API_KEY is not set');
const wait = (s) => new Promise((r) => setTimeout(r, s * 1000));

async function api(method, path, fields = {}) {
  const url = new URL(API + path);
  const opt = { method, headers: { 'X-API-Key': KEY } };
  if (method === 'GET') for (const [k, v] of Object.entries(fields)) url.searchParams.append(k, v);
  else opt.body = new URLSearchParams(fields); // sent as application/x-www-form-urlencoded
  const res = await fetch(url, opt);
  if (res.status === 429) { await wait(Number(res.headers.get('retry-after') || 5)); return api(method, path, fields); }
  const json = await res.json().catch(() => ({}));
  if (json.code !== 1) throw new Error(json.msg || `HTTP ${res.status}`);
  return json.data ?? {};
}

const [service = 'telegram', country = 'id'] = process.argv.slice(2);
const { operators = [] } = await api('GET', '/api/activation/quote', { service, country });
if (!operators.length) { console.error('No numbers now — try another country'); process.exit(1); }
const op = operators[0];

const idempotency_key = randomBytes(16).toString('hex');
const { order } = await api('POST', '/api/activation/allocate', {
  service, country, operator: op.operator, expected_price: op.price, idempotency_key,
});
console.log(`Number ${order.phone} via ${op.operator} for $${order.amount}`);

const deadline = (order.expires_at ?? Date.now() / 1000 + 600) * 1000;
while (Date.now() < deadline) {
  await wait(5);
  const { order: o } = await api('POST', '/api/activation/poll', { order_no: order.order_no });
  if (o.sms?.length) { console.log('Code:', o.sms_code || o.sms.at(-1).code, '-', o.sms.at(-1).text); process.exit(0); }
  if (['cancelled', 'failed', 'finished'].includes(o.status)) { console.log('Ended:', o.status); process.exit(0); }
}
await api('POST', '/api/activation/cancel', { order_no: order.order_no });
console.log('No SMS — refunded');
