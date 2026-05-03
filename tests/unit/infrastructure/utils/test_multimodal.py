import pytest
from sdpj.infrastructure.utils.multimodal import (
    text_to_audio, audio_to_text,
    text_to_image, text_to_video,
)


def test_audio_roundtrip():
    text = "hello world"
    assert audio_to_text(text_to_audio(text)) == text


def test_audio_unicode_roundtrip():
    text = "你好世界"
    assert audio_to_text(text_to_audio(text)) == text


def test_audio_empty_string():
    assert audio_to_text(text_to_audio("")) == ""


def test_text_to_image_returns_png():
    data = text_to_image("test")
    assert data[:4] == b"\x89PNG"


def test_text_to_video_returns_gif():
    data = text_to_video("test")
    assert data[:3] == b"GIF"
