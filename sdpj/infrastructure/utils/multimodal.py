"""UtilsLib 多模态处理工具"""
from PIL import Image
from io import BytesIO


def text_to_image(text: str, width: int = 400, height: int = 100) -> bytes:
    """文本生成图像"""
    img = Image.new('RGB', (width, height), color='white')
    # 简化实现：返回空白图像
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def image_to_text(image_data: bytes) -> str:
    """图像提取文本（简化实现）"""
    # 实际应使用 OCR，这里简化返回占位符
    return "[Image content]"
