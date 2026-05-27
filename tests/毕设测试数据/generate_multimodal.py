"""为 test.jsonl 中的每条 PoC 生成图片(png)和音频(mp3)."""

import asyncio
import base64
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sdpj.infrastructure.utils.multimodal import build_multimodal_content

INPUT_FILE = os.path.join(os.path.dirname(__file__), "数据集", "test.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "多模态")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_FILE, encoding="utf-8") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    for i, sample in enumerate(samples, 1):
        poc = sample["poc"]
        subtype = sample["subtype"]
        print(f"[{i}/{len(samples)}] subtype={subtype}")
        print(f"  PoC: {poc[:80]}...")

        # 生成图片
        img_content = await build_multimodal_content(poc, "png")
        img_item = next(c for c in img_content if c["type"] == "image_url")
        data_uri = img_item["image_url"]["url"]
        b64_data = data_uri.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_data)
        img_path = os.path.join(OUTPUT_DIR, f"poc_{i}_{subtype}.png")
        with open(img_path, "wb") as fp:
            fp.write(img_bytes)
        print(f"  -> 图片: {img_path} ({len(img_bytes)} bytes)")

        # 生成音频
        audio_content = await build_multimodal_content(poc, "mp3")
        audio_item = next(c for c in audio_content if c["type"] == "input_audio")
        b64_audio = audio_item["input_audio"]["data"]
        audio_bytes = base64.b64decode(b64_audio)
        audio_path = os.path.join(OUTPUT_DIR, f"poc_{i}_{subtype}.mp3")
        with open(audio_path, "wb") as fp:
            fp.write(audio_bytes)
        print(f"  -> 音频: {audio_path} ({len(audio_bytes)} bytes)")

    print(f"\n完成,输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
