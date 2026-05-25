"""SecureCommManager 安全通信管理模块

负责 HTTPS/TLS 证书管理和安全通信配置。
原 RSA 加解密职责已移除，传输层安全由 HTTPS/TLS 保障。

职责：
1. SSL/TLS 证书管理（生成自签名证书、加载、路径查询）
2. 安全通信配置提供（uvicorn SSL 参数）
3. 安全响应头配置（HSTS、X-Content-Type-Options、X-Frame-Options）

依赖模块: 无
被依赖模块: StateScheduler, WebUI
"""

from __future__ import annotations

import datetime
import ipaddress
from pathlib import Path
from typing import Optional

from .secure_comm_manager_interface import SecureCommManagerInterface


class SecureCommManager(SecureCommManagerInterface):
    """安全通信管理模块实现"""

    # 默认证书目录：项目根目录/certs/
    _DEFAULT_CERT_DIR = "certs"
    _CERT_FILENAME = "cert.pem"
    _KEY_FILENAME = "key.pem"

    def __init__(self, cert_dir: Optional[str] = None):
        """初始化安全通信管理器。

        Args:
            cert_dir: 证书目录的绝对或相对路径，默认为项目根目录/certs/
        """
        if cert_dir:
            self._cert_dir = Path(cert_dir).resolve()
        else:
            # 项目根目录 = sdpj/core/ 的上两级
            self._cert_dir = Path(__file__).resolve().parents[2] / self._DEFAULT_CERT_DIR

        self._cert_path = self._cert_dir / self._CERT_FILENAME
        self._key_path = self._cert_dir / self._KEY_FILENAME

    # ── 证书管理 ──

    def ensure_certificates(self) -> tuple[str, str]:
        """确保证书文件存在，不存在则自动生成自签名证书。

        生成的证书包含 SAN 扩展，覆盖 localhost / 127.0.0.1 / ::1，
        有效期 10 年，仅供本地开发使用。

        Returns:
            (cert_path, key_path) 证书和私钥的绝对路径字符串
        """
        if self._cert_path.exists() and self._key_path.exists():
            return str(self._cert_path), str(self._key_path)

        return self._generate_self_signed_cert()

    def _generate_self_signed_cert(self) -> tuple[str, str]:
        """生成自签名 SSL 证书。"""
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        self._cert_dir.mkdir(parents=True, exist_ok=True)

        # 生成 RSA-2048 私钥
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Subject / Issuer（自签名，两者相同）
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "SDPJ-System Dev"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SDPJ-System"),
            ]
        )

        # SAN：覆盖本地开发所有可能的地址
        san = x509.SubjectAlternativeName(
            [
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(san, critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        # 写入磁盘
        self._key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        self._cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

        print("[SecureCommManager] Self-signed certificate generated:")
        print(f"  Cert: {self._cert_path}")
        print(f"  Key:  {self._key_path}")

        return str(self._cert_path), str(self._key_path)

    # ── SSL 配置 ──

    def get_ssl_kwargs(self) -> dict:
        """获取 uvicorn 启动所需的 SSL 关键字参数。

        Returns:
            {"ssl_certfile": str, "ssl_keyfile": str}
            如果证书不存在则返回空 dict
        """
        cert_path, key_path = self.ensure_certificates()
        return {
            "ssl_certfile": cert_path,
            "ssl_keyfile": key_path,
        }

    # ── 安全头 ──

    def get_security_headers(self) -> dict[str, str]:
        """获取应附加到所有 HTTPS 响应的安全头。

        Returns:
            {header_name: header_value} 映射
        """
        return {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
