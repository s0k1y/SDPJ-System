import base64
import codecs


class BaseCodec:  # noqa: D101
    @staticmethod
    def encode_base16(text):  # noqa: ANN001, ANN205, D102
        return base64.b16encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base16(encoded):  # noqa: ANN001, ANN205, D102
        return base64.b16decode(encoded.encode("ascii"), casefold=True).decode("utf-8")

    @staticmethod
    def encode_base32(text):  # noqa: ANN001, ANN205, D102
        return base64.b32encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base32(encoded):  # noqa: ANN001, ANN205, D102
        return base64.b32decode(encoded.encode("ascii"), casefold=True).decode("utf-8")

    @staticmethod
    def encode_base64(text):  # noqa: ANN001, ANN205, D102
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base64(encoded):  # noqa: ANN001, ANN205, D102
        padding = 4 - len(encoded) % 4
        if padding != 4:  # noqa: PLR2004
            encoded += "=" * padding
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")

    @staticmethod
    def encode_base85(text):  # noqa: ANN001, ANN205, D102
        return base64.b85encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base85(encoded):  # noqa: ANN001, ANN205, D102
        return base64.b85decode(encoded.encode("ascii")).decode("utf-8")


class Rot13Codec:  # noqa: D101
    @staticmethod
    def encode(text):  # noqa: ANN001, ANN205, D102
        return codecs.encode(text, "rot_13")

    @staticmethod
    def decode(text):  # noqa: ANN001, ANN205, D102
        return codecs.encode(text, "rot_13")


class HexCodec:  # noqa: D101
    @staticmethod
    def encode(text):  # noqa: ANN001, ANN205, D102
        return text.encode("utf-8").hex()

    @staticmethod
    def decode(encoded):  # noqa: ANN001, ANN205, D102
        return bytes.fromhex(encoded).decode("utf-8")


class CaesarCipher:  # noqa: D101
    @staticmethod
    def encrypt(text, shift=3):  # noqa: ANN001, ANN205, D102
        result = []
        for char in text:
            if "A" <= char <= "Z":
                result.append(chr((ord(char) - ord("A") + shift) % 26 + ord("A")))
            elif "a" <= char <= "z":
                result.append(chr((ord(char) - ord("a") + shift) % 26 + ord("a")))
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def decrypt(text, shift=3):  # noqa: ANN001, ANN205, D102
        return CaesarCipher.encrypt(text, -shift)


class MorseCodec:  # noqa: D101
    MORSE_TABLE = {  # noqa: RUF012
        "A": ".-",
        "B": "-...",
        "C": "-.-.",
        "D": "-..",
        "E": ".",
        "F": "..-.",
        "G": "--.",
        "H": "....",
        "I": "..",
        "J": ".---",
        "K": "-.-",
        "L": ".-..",
        "M": "--",
        "N": "-.",
        "O": "---",
        "P": ".--.",
        "Q": "--.-",
        "R": ".-.",
        "S": "...",
        "T": "-",
        "U": "..-",
        "V": "...-",
        "W": ".--",
        "X": "-..-",
        "Y": "-.--",
        "Z": "--..",
        "0": "-----",
        "1": ".----",
        "2": "..---",
        "3": "...--",
        "4": "....-",
        "5": ".....",
        "6": "-....",
        "7": "--...",
        "8": "---..",
        "9": "----.",
        ".": ".-.-.-",
        ",": "--..--",
        "?": "..--..",
        "'": ".----.",
        "!": "-.-.--",
        "/": "-..-.",
        "(": "-.--.",
        ")": "-.--.-",
        "&": ".-...",
        ":": "---...",
        ";": "-.-.-.",
        "=": "-...-",
        "+": ".-.-.",
        "-": "-....-",
        "_": "..--.-",
        '"': ".-..-.",
        "$": "...-..-",
        "@": ".--.-.",
        " ": "/",
    }

    REVERSE_MORSE = {v: k for k, v in MORSE_TABLE.items()}  # noqa: RUF012

    @staticmethod
    def encode(text):  # noqa: ANN001, ANN205, D102
        parts = []
        for char in text.upper():
            if char in MorseCodec.MORSE_TABLE:
                parts.append(MorseCodec.MORSE_TABLE[char])
            else:
                parts.append(char)
        return " ".join(parts)

    @staticmethod
    def decode(encoded):  # noqa: ANN001, ANN205, D102
        words = encoded.split(" / ")
        decoded_words = []
        for word in words:
            letters = word.split(" ")
            decoded_letters = []
            for letter in letters:
                if letter in MorseCodec.REVERSE_MORSE:
                    decoded_letters.append(MorseCodec.REVERSE_MORSE[letter])
                elif letter == "":
                    continue
                else:
                    decoded_letters.append(letter)
            decoded_words.append("".join(decoded_letters))
        return " ".join(decoded_words)


class VigenereCipher:  # noqa: D101
    @staticmethod
    def encrypt(text, key):  # noqa: ANN001, ANN205, D102
        if not key:
            msg = "密钥不能为空"
            raise ValueError(msg)
        if not key.isalpha():
            msg = "密钥必须只包含字母字符"
            raise ValueError(msg)
        key = key.upper()
        result = []
        key_index = 0
        for char in text:
            if "A" <= char <= "Z":
                shift = ord(key[key_index % len(key)]) - ord("A")
                result.append(chr((ord(char) - ord("A") + shift) % 26 + ord("A")))
                key_index += 1
            elif "a" <= char <= "z":
                shift = ord(key[key_index % len(key)]) - ord("A")
                result.append(chr((ord(char) - ord("a") + shift) % 26 + ord("a")))
                key_index += 1
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def decrypt(text, key):  # noqa: ANN001, ANN205, D102
        if not key:
            msg = "密钥不能为空"
            raise ValueError(msg)
        if not key.isalpha():
            msg = "密钥必须只包含字母字符"
            raise ValueError(msg)
        key = key.upper()
        result = []
        key_index = 0
        for char in text:
            if "A" <= char <= "Z":
                shift = ord(key[key_index % len(key)]) - ord("A")
                result.append(chr((ord(char) - ord("A") - shift) % 26 + ord("A")))
                key_index += 1
            elif "a" <= char <= "z":
                shift = ord(key[key_index % len(key)]) - ord("A")
                result.append(chr((ord(char) - ord("a") - shift) % 26 + ord("a")))
                key_index += 1
            else:
                result.append(char)
        return "".join(result)


class ASCIICodec:  # noqa: D101
    @staticmethod
    def encode(text):  # noqa: ANN001, ANN205, D102
        return " ".join(str(ord(c)) for c in text)

    @staticmethod
    def decode(encoded):  # noqa: ANN001, ANN205, D102
        codes = encoded.strip().split()
        return "".join(chr(int(code)) for code in codes)


class UnicodeCodec:  # noqa: D101
    @staticmethod
    def encode(text):  # noqa: ANN001, ANN205, D102
        return " ".join(f"U+{ord(c):04X}" for c in text)

    @staticmethod
    def decode(encoded):  # noqa: ANN001, ANN205, D102
        codes = encoded.strip().split()
        result = []
        for code in codes:
            code = code.upper().replace("U+", "")  # noqa: PLW2901
            result.append(chr(int(code, 16)))
        return "".join(result)


CIPHERS: dict[str, dict[str, Any]] = {
    "base16": {
        "encode": BaseCodec.encode_base16,
        "decode": BaseCodec.decode_base16,
    },
    "base32": {
        "encode": BaseCodec.encode_base32,
        "decode": BaseCodec.decode_base32,
    },
    "base64": {
        "encode": BaseCodec.encode_base64,
        "decode": BaseCodec.decode_base64,
    },
    "base85": {
        "encode": BaseCodec.encode_base85,
        "decode": BaseCodec.decode_base85,
    },
    "rot13": {
        "encode": Rot13Codec.encode,
        "decode": Rot13Codec.decode,
    },
    "hex": {
        "encode": HexCodec.encode,
        "decode": HexCodec.decode,
    },
    "caesar": {
        "encode": CaesarCipher.encrypt,
        "decode": CaesarCipher.decrypt,
    },
    "morse": {
        "encode": MorseCodec.encode,
        "decode": MorseCodec.decode,
    },
    "vigenere": {
        "encode": VigenereCipher.encrypt,
        "decode": VigenereCipher.decrypt,
    },
    "ascii": {
        "encode": ASCIICodec.encode,
        "decode": ASCIICodec.decode,
    },
    "unicode": {
        "encode": UnicodeCodec.encode,
        "decode": UnicodeCodec.decode,
    },
}


def main() -> None:  # noqa: D103
    parser = argparse.ArgumentParser(
        description="古典密码与编码加解密工具包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""支持的编码/密码类型:
  base16, base32, base64, base85, rot13, hex,
  caesar, morse, vigenere, ascii, unicode

示例:
  python crypto_toolkit.py encode base64 "Hello World"
  python crypto_toolkit.py decode base64 "SGVsbG8gV29ybGQ="
  python crypto_toolkit.py encode caesar "Hello" --shift 5
  python crypto_toolkit.py decode caesar "Mjqqt" --shift 5
  python crypto_toolkit.py encode vigenere "Hello" --key KEY
  python crypto_toolkit.py decode vigenere "Rijvs" --key KEY
""",
    )

    subparsers = parser.add_subparsers(dest="action", help="操作类型")

    enc_parser = subparsers.add_parser("encode", help="编码/加密")
    enc_parser.add_argument("cipher", choices=CIPHERS.keys(), help="编码/密码类型")
    enc_parser.add_argument("text", help="要编码的文本")
    enc_parser.add_argument("--shift", type=int, default=3, help="凯撒密码偏移量 (默认: 3)")
    enc_parser.add_argument("--key", type=str, default="", help="维吉尼亚密码密钥")

    dec_parser = subparsers.add_parser("decode", help="解码/解密")
    dec_parser.add_argument("cipher", choices=CIPHERS.keys(), help="编码/密码类型")
    dec_parser.add_argument("text", help="要解码的文本")
    dec_parser.add_argument("--shift", type=int, default=3, help="凯撒密码偏移量 (默认: 3)")
    dec_parser.add_argument("--key", type=str, default="", help="维吉尼亚密码密钥")

    args = parser.parse_args()

    if args.action is None:
        parser.print_help()
        return

    cipher_name = args.cipher
    action = args.action

    try:
        if cipher_name == "caesar":
            if action == "encode":
                CaesarCipher.encrypt(args.text, args.shift)
            else:
                CaesarCipher.decrypt(args.text, args.shift)
        elif cipher_name == "vigenere":
            if not args.key:
                sys.exit(1)
            if action == "encode":
                VigenereCipher.encrypt(args.text, args.key)
            else:
                VigenereCipher.decrypt(args.text, args.key)
        else:
            func = CIPHERS[cipher_name][action]
            func(args.text)

    except Exception:  # noqa: BLE001
        sys.exit(1)


if __name__ == "__main__":
    main()
