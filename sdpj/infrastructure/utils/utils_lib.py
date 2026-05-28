"""UtilsLib 主模块."""

from . import encoding, file, serialization


class UtilsLib:
    """杂项组件库."""

    # 编码
    encode_text = staticmethod(encoding.encode_text)
    decode_text = staticmethod(encoding.decode_text)

    # 文件
    read_file = staticmethod(file.read_file)
    write_file = staticmethod(file.write_file)
    validate_file_format = staticmethod(file.validate_file_format)

    # 序列化
    serialize_json = staticmethod(serialization.serialize_json)
    deserialize_json = staticmethod(serialization.deserialize_json)
    serialize_yaml = staticmethod(serialization.serialize_yaml)
    deserialize_yaml = staticmethod(serialization.deserialize_yaml)
