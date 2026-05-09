"""SecureCommManager 接口定义

安全通信管理模块接口，负责 HTTPS/TLS 证书管理和安全通信配置。
传输层安全由 HTTPS/TLS 保障，不再需要应用层加解密。
"""

from __future__ import annotations

from typing import Protocol


class SecureCommManagerInterface(Protocol):
    """安全通信管理接口，被 StateScheduler 调用。

    职责：
    1. SSL/TLS 证书管理（生成、加载、路径查询）
    2. 安全通信配置提供（uvicorn SSL 参数、安全头配置）
    3. 安全中间件注册
    """

    def ensure_certificates(self) -> tuple[str, str]:
        """确保证书文件存在，不存在则自动生成。

        Returns:
            (cert_path, key_path) 证书和私钥的绝对路径
        """
        ...

    def get_ssl_kwargs(self) -> dict:
        """获取 uvicorn 启动所需的 SSL 关键字参数。

        Returns:
            {"ssl_certfile": ..., "ssl_keyfile": ...}
            如果证书不可用则返回空 dict
        """
        ...

    def get_security_headers(self) -> dict[str, str]:
        """获取应附加到所有 HTTPS 响应的安全头。

        Returns:
            {header_name: header_value} 映射
        """
        ...
