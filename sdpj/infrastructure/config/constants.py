"""系统常量定义"""
from pathlib import Path

APP_NAME = "SDPJ-System"
APP_VERSION = "1.0.0"

DEFAULT_LOG_DIR = "sdpj/infrastructure/database/logs"
DEFAULT_REPORT_DIR = "sdpj/infrastructure/database/reports"
DEFAULT_EXPORT_DIR = "sdpj/infrastructure/database/reports/exports"
DEFAULT_UPLOAD_DIR = "sdpj/infrastructure/database/uploads"

USER_CONFIG_DIR_NAME = ".sdpj"
SECRET_KEY_FILENAME = "secret.key"
RSA_KEY_FILENAME = "rsa_private.pem"
TOKEN_FILENAME = "token"
USER_ADAPTERS_DIR = "adapters"

SECRET_KEY_BYTES = 32

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

PASSWORD_HASH_ROUNDS = 12

MAX_UPLOAD_SIZE_MB = 50

SUPPORTED_DATASET_FORMATS = (".csv", ".json", ".yaml", ".yml")
SUPPORTED_ADAPTER_FORMAT = ".json"

DETECTION_ALGORITHM_STATIC = "static"
DETECTION_ALGORITHM_DYNAMIC = "dynamic"

LOG_FORMAT_JSON = "json"
LOG_FORMAT_CONSOLE = "console"
