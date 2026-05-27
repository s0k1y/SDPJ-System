"""Run ruff and capture JSON output with proper encoding."""
import subprocess
import json
from collections import defaultdict

result = subprocess.run(
    ["python", "-m", "ruff", "check", "--select=ALL", "--output-format=json", "sdpj/ui/"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)

data = json.loads(result.stdout)

by_file = defaultdict(list)
for item in data:
    fname = item["filename"]
    # Normalize path
    fname = fname.replace("\\", "/")
    by_file[fname].append(item["code"])

# Save as clean JSON
with open("ruff_out.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Print summary
for fname, codes in sorted(by_file.items()):
    c = {}
    for code in codes:
        c[code] = c.get(code, 0) + 1
    total = len(codes)
    parts = ", ".join(f"{k}:{v}" for k, v in sorted(c.items(), key=lambda x: -x[1]))
    print(f"{total:3d} | {fname}")
    print(f"    | {parts}")

print(f"\nTotal: {len(data)} issues")
