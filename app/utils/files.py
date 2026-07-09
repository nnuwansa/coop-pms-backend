# import os
# import shutil
# from datetime import datetime
# from logging import getLogger
#
# from fastapi import UploadFile
#
# from config.config import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_MB, TIME_ZONE
# from exception.exception import UnsupportedFileTypeException, FileTooLargeException, FileDeletionException
#
# logger = getLogger(__name__)
#
#
# async def validate_file(file: UploadFile):
#     if file.content_type not in ALLOWED_MIME_TYPES:
#         raise UnsupportedFileTypeException(f"Unsupported file type: {file.content_type}")
#
#     file.file.seek(0, os.SEEK_END)
#     size_in_mb = file.file.tell() / (1024 * 1024)
#     file.file.seek(0)
#
#     if size_in_mb > MAX_FILE_SIZE_MB:
#         raise FileTooLargeException(f"File too large: {size_in_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)")
#
#
# async def validate_files(files):
#     for file in files:
#         await validate_file(file)
#
#
# def write_file_to_disk(path: str, content: bytes) -> None:
#     """
#     Internal helper to write file content to disk at the specified path.
#     """
#     with open(path, "wb") as out_file:
#         out_file.write(content)
#
#
# def save_attachment(file: UploadFile, folder_path: str) -> str:
#     os.makedirs(folder_path, exist_ok=True)
#     timestamp = datetime.now(TIME_ZONE).strftime("%Y%m%d%H%M%S%f")
#     ext = os.path.splitext(file.filename)[1]
#     safe_filename = f"{timestamp}{ext}"
#     full_path = os.path.join(folder_path, safe_filename)
#
#     contents = file.file.read()
#     write_file_to_disk(full_path, contents)
#     return safe_filename
#
#
# def delete_file(folder_path: str, file_name: str) -> None:
#     """
#     Deletes a file from the filesystem if it exists.
#     Logs warning if file is not found.
#     """
#     file_path = os.path.join(folder_path, file_name)
#     try:
#         if os.path.isfile(file_path):
#             os.remove(file_path)
#             logger.info(f"File deleted: {file_path}")
#         else:
#             logger.warning(f"File not found for deletion: {file_path}")
#     except Exception as e:
#         logger.error(f"Failed to delete file {file_path}: {str(e)}")
#         raise FileDeletionException('Unable to delete file')
#
#
# def duplicate_file(source_path: str, destination_path: str, file_name: str) -> str:
#     """
#     Duplicates all files from the source folder to the destination folder.
#     """
#     os.makedirs(destination_path, exist_ok=True)
#     timestamp = datetime.now(TIME_ZONE).strftime("%Y%m%d%H%M%S%f")
#     ext = os.path.splitext(file_name)[1]
#     destination_file_name = f"{timestamp}{ext}"
#     source_file = os.path.join(source_path, file_name)
#     destination_file = os.path.join(destination_path, destination_file_name)
#
#     if not os.path.isfile(source_file):
#         logger.warning(f"Source file not found for duplication: {source_file}")
#
#     shutil.copy2(source_file, destination_file)
#     logger.info(f"Duplicated file from {source_file} to {destination_file}")
#     return destination_file_name



import os
import uuid
from typing import List, Tuple

from fastapi import UploadFile

from exception.exception import FileTooLargeException

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB — change to your actual limit
ACCEPTED_FILE_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]  # keep this in sync with your frontend ACCEPTED_FILE_TYPES


async def validate_files(files: List[UploadFile]):
    for file in (files or []):
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        if size > MAX_ATTACHMENT_SIZE:
            raise FileTooLargeException(
                f"'{file.filename}' exceeds the maximum allowed size of "
                f"{MAX_ATTACHMENT_SIZE // (1024 * 1024)}MB"
            )


def save_attachment(file: UploadFile, folder_path: str) -> Tuple[str, int]:
    os.makedirs(folder_path, exist_ok=True)
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    saved_name = f"{uuid.uuid4().hex}_{file.filename}"
    with open(os.path.join(folder_path, saved_name), "wb") as f:
        f.write(file.file.read())

    return saved_name, size


def delete_file(folder_path: str, file_name: str):
    file_path = os.path.join(folder_path, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)


def duplicate_file(src_folder: str, dst_folder: str, file_name: str) -> str:
    os.makedirs(dst_folder, exist_ok=True)
    src_path = os.path.join(src_folder, file_name)
    new_name = f"{uuid.uuid4().hex}_{file_name}"
    dst_path = os.path.join(dst_folder, new_name)
    with open(src_path, "rb") as src, open(dst_path, "wb") as dst:
        dst.write(src.read())
    return new_name