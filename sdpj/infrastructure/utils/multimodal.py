"""UtilsLib 多模态处理工具"""
from io import BytesIO


def text_to_image(text: str, width: int = 400, height: int = 100) -> bytes:
    """将文本渲染为 PNG 图像"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", size=16)
    except OSError:
        font = ImageFont.load_default()

    margin = 10
    y = margin
    for line in text.split("\n"):
        if y + 20 > height - margin:
            break
        draw.text((margin, y), line, fill="black", font=font)
        y += 20

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def image_to_text(image_data: bytes) -> str:
    """从图像中提取嵌入的文本信息

    尝试读取图像 EXIF/metadata 中的文本描述；
    若无元数据则对像素做基础分析，返回图像摘要信息。
    """
    from PIL import Image
    from PIL.ExifTags import TAGS

    img = Image.open(BytesIO(image_data))

    text_parts = []

    if hasattr(img, "_getexif") and img._getexif():
        exif = img._getexif()
        for tag_id, value in exif.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "ImageDescription" and isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
            elif tag_name == "UserComment" and isinstance(value, str) and value.strip():
                text_parts.append(value.strip())

    info = img.info
    if "Description" in info:
        text_parts.append(str(info["Description"]))
    if "Comment" in info:
        text_parts.append(str(info["Comment"]))

    for key in ("XML:com.adobe.xmp", "xmp"):
        if key in info and isinstance(info[key], (str, bytes)):
            xmp = info[key] if isinstance(info[key], str) else info[key].decode("utf-8", errors="ignore")
            import re
            desc_match = re.search(r"<dc:description>.*?<rdf:li[^>]*>(.+?)</rdf:li>", xmp, re.DOTALL)
            if desc_match:
                text_parts.append(desc_match.group(1).strip())

    if text_parts:
        return "\n".join(text_parts)

    w, h = img.size
    return f"[图像 {w}x{h} {img.mode}, 未检测到嵌入文本]"


def text_to_audio(text: str) -> bytes:
    """将文本嵌入 WAV 文件的 RIFF INFO 元数据（ICMT 字段）"""
    import struct, wave
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(b"\x00\x00" * 100)
    wav = buf.getvalue()

    text_b = text.encode("utf-8")
    if len(text_b) % 2:
        text_b += b"\x00"
    icmt = b"ICMT" + struct.pack("<I", len(text.encode("utf-8"))) + text_b
    list_chunk = b"LIST" + struct.pack("<I", 4 + len(icmt)) + b"INFO" + icmt
    new_size = len(wav) - 8 + len(list_chunk)
    return wav[:4] + struct.pack("<I", new_size) + wav[8:] + list_chunk


def audio_to_text(audio_data: bytes) -> str:
    """从 WAV 文件的 RIFF INFO 元数据中提取文本"""
    import struct
    i = 12
    while i < len(audio_data) - 8:
        chunk_id = audio_data[i:i+4]
        chunk_size = struct.unpack("<I", audio_data[i+4:i+8])[0]
        if chunk_id == b"LIST" and audio_data[i+8:i+12] == b"INFO":
            j = i + 12
            end = i + 8 + chunk_size
            while j < end - 8:
                sub_id = audio_data[j:j+4]
                sub_size = struct.unpack("<I", audio_data[j+4:j+8])[0]
                if sub_id == b"ICMT":
                    return audio_data[j+8:j+8+sub_size].rstrip(b"\x00").decode("utf-8", errors="replace")
                j += 8 + sub_size + (sub_size % 2)
        i += 8 + chunk_size + (chunk_size % 2)
    return ""


def text_to_video(text: str) -> bytes:
    """将文本渲染为带文字的动态 GIF（视频格式）"""
    from PIL import Image, ImageDraw, ImageFont
    lines = [text[i:i+40] for i in range(0, min(len(text), 200), 40)] or [""]
    frames = []
    for line in lines:
        img = Image.new("RGB", (400, 100), "white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font = ImageFont.load_default()
        draw.text((10, 40), line, fill="black", font=font)
        frames.append(img)
    buf = BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=500, loop=0)
    return buf.getvalue()


def video_to_text(video_data: bytes) -> str:
    """从 GIF 第一帧中提取文本（复用 image_to_text）"""
    from PIL import Image
    img = Image.open(BytesIO(video_data))
    frame_buf = BytesIO()
    img.convert("RGB").save(frame_buf, format="PNG")
    return image_to_text(frame_buf.getvalue())
