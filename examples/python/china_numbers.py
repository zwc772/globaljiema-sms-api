"""+86 mainland numbers (国内接码): search project -> allocate -> poll -> release.

    python china_numbers.py 小红书
"""
import sys
import time

from globaljiema import call, paid_call

kw = sys.argv[1] if len(sys.argv) > 1 else "小红书"
opts = call("GET", "/api/cnsms/options")
print(f"price ${opts['price']}  wait {opts['ttl']}s  carriers: {', '.join(opts['carriers'])}")

found = call("GET", "/api/cnsms/search", keyword=kw)["rows"]
if not found:
    sys.exit("No such project")
p = found[0]

res = paid_call("/api/cnsms/allocate", project_id=p["project_id"], project_name=p["name"],
                project_token=p["token"], ascription="2", carrier="CMCC", quantity=1)
o = res["orders"][0]
if o["status"] != "active":
    sys.exit(res.get("message") or "no number available")
print("Number:", o["phone"], o.get("province"), o.get("carrier"))

for _ in range(opts["ttl"] // 5):
    time.sleep(5)
    s = call("POST", "/api/cnsms/poll", order_no=o["order_no"])["order"]
    if s["status"] == "received":
        print("Code:", s["sms_code"])
        call("POST", "/api/cnsms/release", order_no=o["order_no"])
        break
    if s["status"] in ("released", "expired", "failed"):
        print("Ended:", s["status"])
        break
