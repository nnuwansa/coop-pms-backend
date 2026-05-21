import os

import pytz
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))

MYSQL_USERNAME = os.getenv('MYSQL_USERNAME')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DB_NAME = os.getenv('MYSQL_DB_NAME')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')

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
