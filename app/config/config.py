import os

import pytz
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))

MYSQL_USERNAME = os.getenv('MYSQL_USERNAME')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DB_NAME = os.getenv('MYSQL_DB_NAME')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')

# BASE_DIR = Path(__file__).resolve().parent.parent
# _attachments_dir = os.getenv('ATTACHMENTS_DIR', str(BASE_DIR / 'letters'))
# ATTACHMENTS_DIR = str(Path(_attachments_dir).resolve()) if os.path.isabs(_attachments_dir) is False else _attachments_dir
ATTACHMENTS_DIR = os.getenv('ATTACHMENTS_DIR', '../../letters')
ATTACHMENTS_URL = os.getenv('ATTACHMENTS_URL', 'http://localhost:8000/attachments')

ALLOWED_MIME_TYPES = os.getenv('ALLOWED_MIME_TYPES', 'image/jpeg,image/jpg,image/png,application/pdf').split(',')
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 3))

TIME_ZONE = pytz.timezone('Asia/Colombo')

ACCESS_SECRET_KEY = os.getenv('ACCESS_SECRET_KEY')
REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY')

ACCESS_TOKEN_ALGORITHM = "HS256"
REFRESH_TOKEN_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 7))

ALLOW_ORIGINS = os.getenv('ALLOW_ORIGINS', 'http://localhost:3000').split(',')
FE_DOMAIN = os.getenv('FE_DOMAIN', 'localhost')  # Set to your frontend domain
HTTPS_ENABLED = os.getenv('HTTPS_ENABLED', 'false').lower() == 'true'  # Set to False in development if not using HTTPS

PENDING_REMINDER_DAYS = int(os.getenv("PENDING_REMINDER_DAYS", "3"))
REMINDER_RESEND_INTERVAL_DAYS = int(os.getenv("REMINDER_RESEND_INTERVAL_DAYS", "1"))

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME')
