"""Receive one SMS verification code.

    python receive_sms.py <service> <country> [max_price]
    python receive_sms.py telegram id 0.50
"""
import sys
import time

from globaljiema import APIError, call, paid_call

service, country = sys.argv[1], sys.argv[2]
max_price = float(sys.argv[3]) if len(sys.argv) > 3 else None

quote = call("GET", "/api/activation/quote", country=country, service=service)
operators = quote.get("operators") or []
if not operators:
    sys.exit(f"No numbers for {service} in {country} right now ({quote.get('hidden', 0)} routes hidden).")

op = operators[0]
print(f"Cheapest operator: {op['operator']}  ${op['price']}  stock={op['count']}  multi_sms={op['multi_sms']}")
if max_price is not None and float(op["price"]) > max_price:
    sys.exit("Above your max price.")

try:
    order = paid_call("/api/activation/allocate", country=country, service=service,
                      operator=op["operator"], expected_price=op["price"])["order"]
except APIError as e:
    sys.exit(f"Allocation failed: {e}")

if order["status"] != "active":
    sys.exit(f"Order {order['order_no']} is {order['status']} (failed orders are refunded).")
print(f"Number {order['phone']}  (order {order['order_no']}) — enter it in {service} now.")

end = order.get("expires_at") or (time.time() + 600)
while time.time() < end:
    time.sleep(5)
    o = call("POST", "/api/activation/poll", order_no=order["order_no"])["order"]
    if o.get("sms"):
        last = o["sms"][-1]
        print(f"Code: {o.get('sms_code') or last.get('code')}   text: {last.get('text')}")
        sys.exit(0)
    if o["status"] in ("cancelled", "failed", "finished"):
        sys.exit(f"Order ended: {o['status']}")

call("POST", "/api/activation/cancel", order_no=order["order_no"])
print("No SMS — cancelled and refunded.")
