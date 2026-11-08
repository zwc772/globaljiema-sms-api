#!/usr/bin/env bash
# GlobalJiema activation with curl + jq.  bash receive_sms.sh telegram id
set -euo pipefail
API=https://globaljiema.com
: "${GLOBALJIEMA_API_KEY:?set GLOBALJIEMA_API_KEY}"
SERVICE=${1:-telegram}; COUNTRY=${2:-id}
g() { curl -sf -H "X-API-Key: $GLOBALJIEMA_API_KEY" "$API$1"; }
p() { local path=$1; shift; curl -sf -H "X-API-Key: $GLOBALJIEMA_API_KEY" -X POST "$API$path" "$@"; }

Q=$(g "/api/activation/quote?country=$COUNTRY&service=$SERVICE")
OP=$(jq -r '.data.operators[0].operator // empty' <<<"$Q")
PRICE=$(jq -r '.data.operators[0].price // empty' <<<"$Q")
[ -n "$OP" ] || { echo "no numbers right now"; exit 1; }
echo "operator $OP  price \$$PRICE"

KEY=$(head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n')
A=$(p /api/activation/allocate -d country="$COUNTRY" -d service="$SERVICE" -d operator="$OP" -d expected_price="$PRICE" -d idempotency_key="$KEY")
[ "$(jq -r .code <<<"$A")" = 1 ] || { jq -r .msg <<<"$A"; exit 1; }
ORDER=$(jq -r .data.order.order_no <<<"$A"); echo "number $(jq -r .data.order.phone <<<"$A")"

for _ in $(seq 120); do
  sleep 5
  S=$(p /api/activation/poll -d order_no="$ORDER")
  if [ "$(jq '.data.order.sms | length' <<<"$S")" -gt 0 ]; then
    echo "code $(jq -r .data.order.sms_code <<<"$S")"; exit 0
  fi
done
p /api/activation/cancel -d order_no="$ORDER" >/dev/null && echo "no SMS - refunded"
