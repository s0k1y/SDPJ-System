"""UtilsLib 主模块"""
from . import crypto, encoding, file, serialization, multimodal


class UtilsLib:
    """杂项组件库"""

    # 加密
    symmetric_encrypt = staticmethod(crypto.symmetric_encrypt)
    symmetric_decrypt = staticmethod(crypto.symmetric_decrypt)
    generate_key = staticmethod(crypto.generate_key)
    hash_password = staticmethod(crypto.hash_password)
    verify_password = staticmethod(crypto.verify_password)

    # 编码
    base64_encode = staticmethod(encoding.base64_encode)
    base64_decode = staticmethod(encoding.base64_decode)
    url_encode = staticmethod(encoding.url_encode)
    url_decode = staticmethod(encoding.url_decode)

    # 文件
    read_file = staticmethod(file.read_file)
    write_file = staticmethod(file.write_file)
    validate_file_format = staticmethod(file.validate_file_format)

    # 序列化
    serialize_json = staticmethod(serialization.serialize_json)
    deserialize_json = staticmethod(serialization.deserialize_json)
    serialize_yaml = staticmethod(serialization.serialize_yaml)
    deserialize_yaml = staticmethod(serialization.deserialize_yaml)

    # 多模态
    text_to_image = staticmethod(multimodal.text_to_image)
    image_to_text = staticmethod(multimodal.image_to_text)
