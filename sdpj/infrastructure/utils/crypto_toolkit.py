import argparse
import base64
import codecs
import sys


class BaseCodec:
    @staticmethod
    def encode_base16(text):
        return base64.b16encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base16(encoded):
        return base64.b16decode(encoded.encode("ascii"), casefold=True).decode("utf-8")

    @staticmethod
    def encode_base32(text):
        return base64.b32encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base32(encoded):
        return base64.b32decode(encoded.encode("ascii"), casefold=True).decode("utf-8")

    @staticmethod
    def encode_base64(text):
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base64(encoded):
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")

    @staticmethod
    def encode_base85(text):
        return base64.b85encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def decode_base85(encoded):
        return base64.b85decode(encoded.encode("ascii")).decode("utf-8")


class Rot13Codec:
    @staticmethod
    def encode(text):
        return codecs.encode(text, "rot_13")

    @staticmethod
    def decode(text):
        return codecs.encode(text, "rot_13")


class HexCodec:
    @staticmethod
    def encode(text):
        return text.encode("utf-8").hex()

    @staticmethod
    def decode(encoded):
        return bytes.fromhex(encoded).decode("utf-8")


class CaesarCipher:
    @staticmethod
    def encrypt(text, shift=3):
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
    def decrypt(text, shift=3):
        return CaesarCipher.encrypt(text, -shift)


class MorseCodec:
    MORSE_TABLE = {
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

    REVERSE_MORSE = {v: k for k, v in MORSE_TABLE.items()}

    @staticmethod
    def encode(text):
        parts = []
        for char in text.upper():
            if char in MorseCodec.MORSE_TABLE:
                parts.append(MorseCodec.MORSE_TABLE[char])
            else:
                parts.append(char)
        return " ".join(parts)

    @staticmethod
    def decode(encoded):
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


class VigenereCipher:
    @staticmethod
    def encrypt(text, key):
        if not key:
            raise ValueError("密钥不能为空")
        if not key.isalpha():
            raise ValueError("密钥必须只包含字母字符")
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
    def decrypt(text, key):
        if not key:
            raise ValueError("密钥不能为空")
        if not key.isalpha():
            raise ValueError("密钥必须只包含字母字符")
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


class ASCIICodec:
    @staticmethod
    def encode(text):
        return " ".join(str(ord(c)) for c in text)

    @staticmethod
    def decode(encoded):
        codes = encoded.strip().split()
        return "".join(chr(int(code)) for code in codes)


class UnicodeCodec:
    @staticmethod
    def encode(text):
        return " ".join(f"U+{ord(c):04X}" for c in text)

    @staticmethod
    def decode(encoded):
        codes = encoded.strip().split()
        result = []
        for code in codes:
            code = code.upper().replace("U+", "")
            result.append(chr(int(code, 16)))
        return "".join(result)


CIPHERS = {
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


def main():
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
                result = CaesarCipher.encrypt(args.text, args.shift)
            else:
                result = CaesarCipher.decrypt(args.text, args.shift)
        elif cipher_name == "vigenere":
            if not args.key:
                print("错误: 维吉尼亚密码需要指定 --key 参数")
                sys.exit(1)
            if action == "encode":
                result = VigenereCipher.encrypt(args.text, args.key)
            else:
                result = VigenereCipher.decrypt(args.text, args.key)
        else:
            func = CIPHERS[cipher_name][action]
            result = func(args.text)

        print(result)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
