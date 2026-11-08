"""Get another code on a number from a previous order (the old order must have received an SMS).

    python same_number_again.py <previous_order_no>
"""
import sys
import time

from globaljiema import call, paid_call

prev = sys.argv[1]
q = call("GET", "/api/activation/again_quote", order_no=prev)
if not q.get("available"):
    sys.exit("This number can't be reused now.")
print(f"{q['phone']} for {q['service']}: ${q['price']}")

order = paid_call("/api/activation/again", order_no=prev, expected_price=q["price"])["order"]
print("New order", order["order_no"])
for _ in range(120):
    time.sleep(5)
    o = call("POST", "/api/activation/poll", order_no=order["order_no"])["order"]
    if o.get("sms"):
        print("Code:", o.get("sms_code"), "|", o["sms"][-1]["text"])
        break
else:
    call("POST", "/api/activation/cancel", order_no=order["order_no"])
    print("No SMS — cancelled.")
