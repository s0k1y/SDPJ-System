"""UtilsLib 异常定义"""


class UtilsLibError(Exception):
    """UtilsLib 基础异常"""


class EncryptionError(UtilsLibError):
    """加密错误"""


class FileError(UtilsLibError):
    """文件错误"""
