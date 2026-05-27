"""构建中文字体子集 — 从 PoC 数据集提取字符集并生成精简字体."""

import json
import os
import subprocess
import sys

DATASET_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "sdpj", "infrastructure", "database", "sample_db", "builtin_datasets",
)
CHARSET_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "charset.txt")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "NotoSansSC-Subset.ttf")
SOURCE_FONT = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "simhei.ttf")


def extract_charset() -> str:
    """从全部 .jsonl 数据集中提取去重字符集."""
    chars: set[str] = set()
    for root, _dirs, files in os.walk(DATASET_DIR):
        for fname in files:
            if not fname.endswith(".jsonl"):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        poc = obj.get("poc", "") or obj.get("text", "")
                        chars.update(poc)
                    except (json.JSONDecodeError, AttributeError):
                        continue
    return "".join(sorted(chars))


def main() -> None:
    charset = extract_charset()
    print(f"Extracted {len(charset)} unique characters")

    os.makedirs(os.path.dirname(CHARSET_PATH), exist_ok=True)
    with open(CHARSET_PATH, "w", encoding="utf-8") as f:
        f.write(charset)
    print(f"Charset saved to {CHARSET_PATH}")

    if not os.path.exists(SOURCE_FONT):
        print(f"Source font not found: {SOURCE_FONT}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "fontTools.subset",
        SOURCE_FONT,
        f"--text-file={CHARSET_PATH}",
        f"--output-file={OUTPUT_PATH}",
    ]
    subprocess.run(cmd, check=True)  # noqa: S603
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"Subset font saved to {OUTPUT_PATH} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
