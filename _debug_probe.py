import os
import time

import requests
import urllib3

urllib3.disable_warnings()
s = requests.Session()
s.verify = False
s.post("https://localhost:8000/api/auth/login", json={"username": "username", "password": "password"})
for i in range(60):
    time.sleep(10)
    r = s.get("https://localhost:8000/api/detection/progress")
    d = r.json()
    groups = d.get("data", {}).get("groups", [])
    if not groups:
        print(f"iter{i+1}: empty", flush=True)
        continue
    g = groups[0]
    stage = g.get("stage_info", {}).get("stage", "?")
    status = g.get("status", "?")
    children = g.get("children", [])
    c0 = children[0] if children else {}
    prog = c0.get("progress", {})
    dyn_remain = g.get("stage_info", {}).get("samples_remaining", "?")
    print(f"iter{i+1}: status={status} stage={stage} child_progress={prog.get('processed','?')}/{prog.get('total','?')} dyn_remaining={dyn_remain}", flush=True)
    if "dynamic" in stage or status == "completed":
        print("===FOUND===")
        if os.path.exists("DEBUG-3f7a.log"):
            with open("DEBUG-3f7a.log", encoding="utf-8") as f:
                print(f.read())
        else:
            print("NO LOG FILE")
        break
