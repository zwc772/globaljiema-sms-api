# GlobalJiema API — Receive SMS Verification Codes Programmatically

**[GlobalJiema](https://globaljiema.com/)** lets you rent temporary phone numbers from 100+ countries and receive SMS verification codes (OTP) for WhatsApp, Telegram, Google, TikTok, OpenAI and hundreds of other services. This repository contains ready-to-run client code for the **GlobalJiema Developer API**.

Full API reference: **https://globaljiema.com/apidoc**

| Feature | Endpoint group |
|---|---|
| One-time SMS activation, 100+ countries | `/api/activation/*` |
| Operator-level routing & live prices | `/api/activation/quote` |
| Re-use the same number for another code | `/api/activation/again` |
| Chinese mainland numbers (+86) | `/api/cnsms/*` |
| Long-term US number rental | `/api/rental/*` |

## Quick start

```bash
export GLOBALJIEMA_API_KEY="your_developer_key"

# Python 3.8+
pip install requests
python examples/python/receive_sms.py telegram id      # service, country

# JavaScript (Node.js 18+, no dependencies)
node examples/javascript/receive_sms.mjs telegram id

# Go 1.20+
go run examples/go/main.go telegram id

# Shell (curl + jq)
bash examples/shell/receive_sms.sh telegram id
```

## Getting an API key

1. Create an account at [globaljiema.com](https://globaljiema.com/) and top up with USDT (1 USDT = 1 USD).
2. Once your verified, paid top-ups reach **100 USDT** in total, generate a key at the top of the [API page](https://globaljiema.com/apidoc).
3. Send it in the `X-API-Key` header. Keep it in an environment variable — never in URLs, front-end code or public repositories.

## How an activation works

```
catalog ──► countries?service= ──► quote (operators + prices, free)
                                         │
                                         ▼
                           allocate (charges balance, idempotent)
                                         │
                       poll every 5 s ◄──┘
                         │          │
                  SMS received    no SMS ──► cancel (refund)
                         │
                  again_quote ──► again   (same number, new code)
```

- **Responses**: `{"code":1,"msg":"...","data":{...}}` — `code=1` is success; `code=0` means a business error (read `msg`). HTTP 200 does not mean success.
- **HTTP errors**: 401 invalid key · 403 developer access not enabled · 429 rate limited (respect `Retry-After`).
- **Idempotency**: paid calls (`allocate`, `again`, `rental/order`, `cnsms/allocate`) require a 16–64 character `idempotency_key`. On timeout, retry with the **same** key — you get the original order back instead of being charged twice.
- **Refunds**: orders without an SMS are refunded automatically when they expire, or immediately via `cancel`.
- **Operators**: `quote` returns `operators[]` sorted by price; pass `operator` to `allocate` to lock a carrier. `premium=true` numbers accept one SMS only.

## Examples

| File | What it does |
|---|---|
| [`examples/python/receive_sms.py`](examples/python/receive_sms.py) | Full activation flow with retry-safe allocation and auto-cancel |
| [`examples/python/same_number_again.py`](examples/python/same_number_again.py) | Receive another code on a number you already used |
| [`examples/python/china_numbers.py`](examples/python/china_numbers.py) | +86 mainland numbers by project keyword |
| [`examples/javascript/receive_sms.mjs`](examples/javascript/receive_sms.mjs) | Node.js 18+ activation flow |
| [`examples/go/main.go`](examples/go/main.go) | Go activation flow (standard library only) |
| [`examples/shell/receive_sms.sh`](examples/shell/receive_sms.sh) | curl + jq script |

## 中文说明

GlobalJiema 是一个全球接码平台，提供 100+ 国家的临时号码、中国大陆手机号接码和美国号码租赁。本仓库是 [GlobalJiema 接码 API](https://globaljiema.com/apidoc) 的多语言调用示例：

- 鉴权：请求头 `X-API-Key`，累计已核实实付充值满 100 USDT 后在 API 页生成密钥；
- 国际接码：`quote` 返回按价格排序的运营商线路（`operators`），`allocate` 时可传 `operator` 锁定线路；
- 未收到短信可调用 `cancel` 退款，有效期结束未收码也会自动退款；
- 国内接码（+86）：`/api/cnsms/search` 搜索项目后取号，统一 $1 / 个，20 分钟内未收到验证码自动退款。

更多教程见 [GlobalJiema 博客](https://globaljiema.com/blog)。

## Notes

- Temporary numbers are recycled after the order ends. Use them for one-time verification only — not for accounts that need long-term login, password recovery or payments.
- Follow the terms of the services you verify with and the laws where you operate.
- Rate limits: about 120 read requests and 30 orders per minute per IP.

## Links

- Website: https://globaljiema.com/
- API reference: https://globaljiema.com/apidoc
- Chinese numbers (国内接码): https://globaljiema.com/cn
- Number rental: https://globaljiema.com/tel
- Blog & guides: https://globaljiema.com/blog

## License

MIT
