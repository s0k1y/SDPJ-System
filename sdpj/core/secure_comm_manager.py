import base64
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

from .secure_comm_manager_interface import SecureCommManagerInterface


class SecureCommManager:
    def __init__(self, key_path: Path | None = None):
        if key_path and key_path.exists():
            self._rsa_private = serialization.load_pem_private_key(
                key_path.read_bytes(), password=None
            )
        else:
            self._rsa_private = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            if key_path:
                key_path.parent.mkdir(parents=True, exist_ok=True)
                key_path.write_bytes(self._rsa_private.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ))
        self._rsa_public = self._rsa_private.public_key()

    def get_public_key_spki_b64(self) -> str:
        der = self._rsa_public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return base64.b64encode(der).decode()

    def encrypt_credentials(self, plaintext: str) -> bytes:
        return self._rsa_public.encrypt(
            plaintext.encode(),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

    def decrypt_credentials(self, ciphertext: bytes) -> str:
        if len(ciphertext) < 256:
            raise ValueError("密文长度不足")
        try:
            return self._rsa_private.decrypt(
                ciphertext,
                padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
            ).decode()
        except Exception as e:
            raise ValueError(f"解密失败: {e}")

    def decrypt_from_client(self, ciphertext: bytes) -> str:
        return self.decrypt_credentials(ciphertext)

