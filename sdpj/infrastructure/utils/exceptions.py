"""UtilsLib 异常定义"""


class UtilsLibError(Exception):
    """UtilsLib 基础异常"""
    pass


class EncryptionError(UtilsLibError):
    """加密错误"""
    pass


class FileError(UtilsLibError):
    """文件错误"""
    pass
