import os
from datetime import datetime, timezone
from io import BytesIO
from logging import getLogger
from typing import Optional, List, Dict

from fastapi import UploadFile
from openpyxl.workbook import Workbook
from sqlalchemy.orm import Session

from config.config import ATTACHMENTS_URL, ATTACHMENTS_DIR, TIME_ZONE
from config.constant import LETTERS_EXCEL_HEADERS
from crud.letter import (save_letter, get_active_letter, update_letter, get_all_letter, code_exist,
                         update_letter_attribute, validate_attribute, letters_excel_data, get_letter_count,
                         get_all_status_counts)
from db.models.models import Letter, LetterAttachment
from exception.exception import NoDataFoundException, CodeExistException, LetterNotFoundException
from models.history import HistoryModelOut
from models.letter import LetterModelIn, LetterFilter, LetterModelOut, LetterModelOutOne, LetterModelOutList, \
    RemarksModelOut, AttachmentModelOut, IdNameModelOut, LetterExcelFilter
from models.system_user import SystemUserWithPermissionsModelOut
from service.history import generate_history
from utils.files import validate_files, save_attachment, delete_file, duplicate_file

logger = getLogger(__name__)


async def create_letter(letter_model: LetterModelIn, db: Session) -> Dict:
    logger.info("Create letter process started")

    if await code_exist(letter_model.code, db):
        raise CodeExistException(f"Letter with code {letter_model.code} is already exist.")

    letter = Letter(**letter_model.model_dump())
    letter.status_id = 1
    saved_letter = await save_letter(letter, db)

    logger.info("Create letter process ended")
    return {'id': saved_letter.id, 'code': saved_letter.code}


async def get_letter_by_id(
        letter_id: int,
        current_user: SystemUserWithPermissionsModelOut,
        db: Session
) -> LetterModelOutOne:
    logger.info("Fetch letter process started")
    letter_db = await get_active_letter(letter_id, db)

    if not letter_db:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found.")

    related_letters = list({*letter_db.related_letters1, *letter_db.related_letters2})

    history = []
    if 'letter.history' in current_user.permissions:
        history = [HistoryModelOut.model_validate(letter) for letter in reversed(letter_db.history)]

    remarks = []
    if 'remark.view' in current_user.permissions:
        remarks = [
            RemarksModelOut(
                id=remark.id,
                content=remark.content,
                create_datetime=remark.create_datetime,
                department=remark.department,
                status=remark.status,
                assignee=remark.assignee,
                attachments=await _make_remark_attachments(remark.attachments, letter_id, remark.id),
            )
            for remark in reversed(letter_db.remarks) if remark.is_active
        ]

    letter_response = LetterModelOutOne(
        id=letter_db.id,
        code=letter_db.code,
        received_datetime=letter_db.received_datetime,
        create_datetime=letter_db.create_datetime,
        subject=letter_db.subject,
        other=letter_db.other,
        content=letter_db.content,
        sender=letter_db.sender,
        email=letter_db.email,
        telephone=letter_db.telephone,
        source=IdNameModelOut.model_validate(letter_db.source) if letter_db.source else None,
        organization=IdNameModelOut.model_validate(letter_db.organization) if letter_db.organization else None,
        remarks=remarks,
        history=history,
        department=IdNameModelOut.model_validate(letter_db.department) if letter_db.department else None,
        status=IdNameModelOut.model_validate(letter_db.status) if letter_db.status else None,
        assignee=IdNameModelOut(
            id=letter_db.assignee.id,
            name=f"{letter_db.assignee.first_name} {letter_db.assignee.last_name}",
        ) if letter_db.assignee else None,
        related_letters=related_letters,
        attachments=await _make_attachments(letter_db.attachments, letter_id)
    )

    logger.info("Fetch letter process end")
    return letter_response


async def _make_attachments(attachments: List, letter_id: int) -> List[AttachmentModelOut]:
    return [
        AttachmentModelOut(
            id=attachment.id,
            filename=attachment.file_name,
            title=attachment.title,
            create_datetime=attachment.create_datetime,
            url=f"{ATTACHMENTS_URL}/letter_{letter_id}/{attachment.file_name}"
        )
        for attachment in attachments
    ]


async def _make_remark_attachments(attachments: List, letter_id: int, remark_id: int) -> List[AttachmentModelOut]:
    return [
        AttachmentModelOut(
            id=attachment.id,
            filename=attachment.file_name,
            title=attachment.title,
            create_datetime=attachment.create_datetime,
            url=f"{ATTACHMENTS_URL}/letter_{letter_id}/remark_{remark_id}/{attachment.file_name}"
        )
        for attachment in attachments
    ]


async def update_letter_by_id(letter_id: int, letter_model: LetterModelIn, db: Session) -> LetterModelOut:
    logger.info("Update letter process started")

    letter_db = await get_active_letter(letter_id, db)
    if not letter_db:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    if letter_model.code != letter_db.code and await code_exist(letter_model.code, db):
        raise CodeExistException(f"Letter with code {letter_model.code} is already exist")

    updated_letter = letter_model.model_dump()
    for field, value in updated_letter.items():
        setattr(letter_db, field, value)

    saved_letter = await update_letter(letter_db, db)
    letter_response = LetterModelOut.model_validate(saved_letter)

    logger.info("Update letter process ended")
    return letter_response


async def get_list_letters(
        filters: Optional[LetterFilter],
        page: int,
        page_size: int,
        current_user: SystemUserWithPermissionsModelOut,
        db: Session
):
    logger.info("Fetch letter process started")

    offset = (page - 1) * page_size
    total, letters_db = await get_all_letter(offset, page_size, filters, current_user, db)
    letters_response = [
        LetterModelOutList(
            id=letter.id,
            code=letter.code,
            create_datetime=letter.received_datetime,
            subject=letter.subject,
            department=letter.department.name if letter.department else None,
            status=letter.status.name if letter.status else None,
            organization=letter.organization.name if letter.organization else None,
            assignee=f"{letter.assignee.first_name} {letter.assignee.last_name}" if letter.assignee else None,
            other=letter.other,
        )
        for letter in letters_db
    ]

    logger.info("Fetch letter process ended")
    return total, letters_response


async def delete_letter_by_id(letter_id: int, db: Session) -> int:
    logger.info("Delete letter process started")

    letter_db = await get_active_letter(letter_id, db)
    if not letter_db:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    letter_db.is_active = False
    saved_letter = await update_letter(letter_db, db)

    logger.info("Delete letter process ended")
    return saved_letter.id


async def bind_letter_attachment(letter_id: int, attachments: List[UploadFile], db: Session) -> List[str]:
    logger.info("Binding attachment process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise LetterNotFoundException(f"Letter not found for ID: {letter_id}")

    await validate_files(attachments)

    attachment_names = []
    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}")

    for file in attachments:
        saved_file_name = save_attachment(file, folder_path)
        db.add(LetterAttachment(
            letter_id=letter_id,
            title=file.filename,
            file_name=saved_file_name
        ))
        attachment_names.append(file.filename)

    db.commit()

    logger.info("Binding attachment process end")
    return attachment_names


async def update_letter_attachments(letter_id: int, new_files: List[UploadFile], db: Session) -> List[str]:
    logger.info("Update letter attachment process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}")
    for attachment in letter.attachments:
        db.delete(attachment)
        delete_file(folder_path, attachment.file_name)

    new_filenames = []
    for file in new_files:
        filename = save_attachment(file, folder_path)
        db.add(LetterAttachment(
            letter_id=letter_id,
            title=file.filename,
            file_name=filename
        ))
        new_filenames.append(filename)

    db.commit()

    logger.info("Update letter attachment process end")
    return new_filenames


async def switch_letter_attribute(
        letter_id: int,
        attribute: str,
        current_id: int,
        next_id: int,
        current_user: SystemUserWithPermissionsModelOut,
        db: Session
):
    logger.info("Switch letter attribute process start")
    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    current_value = getattr(letter, f"{attribute}_id", None)
    if current_value is not None:
        if current_value != current_id:
            raise NoDataFoundException(f"The {attribute} mismatch with current_id")

        current_entity = await validate_attribute(attribute, current_id, db)
    else:
        current_entity = None

    next_entity = await validate_attribute(attribute, next_id, db)
    if not next_entity:
        raise NoDataFoundException(f"The {attribute} for ID {next_id} is not found")

    updated_letter = await update_letter_attribute(letter, attribute, next_id, db)
    logger.info("Switch letter attribute process end")

    await generate_history(
        current_entity,
        next_entity,
        attribute,
        f'{current_user.first_name} {current_user.last_name}',
        current_user.email,
        letter_id,
        db
    )
    logger.info("History persisting process end")

    return {'letter_id': updated_letter.id,
            'attribute': attribute,
            'current_id': next_id,
            'previous_id': current_id}


async def letters_excel(filters: LetterExcelFilter, current_user: SystemUserWithPermissionsModelOut, db: Session):
    logger.info("Excel generation process started")

    rows = await letters_excel_data(db, current_user, filters)

    if filters.columns:
        selected_headers = [h for h in LETTERS_EXCEL_HEADERS if h[1] in filters.columns]
    else:
        selected_headers = LETTERS_EXCEL_HEADERS

    wb = Workbook()
    ws = wb.active
    ws.title = "Letters"
    ws.append([h[0] for h in selected_headers])

    for obj in rows:
        row_data = []
        for _, col_name in selected_headers:
            if "." in col_name:
                parent, child = col_name.split(".")
                value = getattr(getattr(obj, parent), child) if getattr(obj, parent) else None
            elif col_name == "assignee":
                value = f"{obj.assignee.first_name} {obj.assignee.last_name}" if obj.assignee else None
            elif col_name == "attachments":
                value = len(obj.attachments) if obj.attachments else 0
            elif col_name in ["received_datetime", "create_datetime", "update_datetime"]:
                value = getattr(obj, col_name).replace(tzinfo=timezone.utc).astimezone(TIME_ZONE).strftime(
                    "%Y-%m-%d")
            else:
                value = getattr(obj, col_name)
            row_data.append(value)
        ws.append(row_data)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    logger.info("Excel generation process end")
    return output


async def generate_letter_code(datetime_utc: datetime, db: Session) -> str:
    logger.info("Generate letter code process started")

    date_local = datetime_utc.astimezone(TIME_ZONE)
    year_utc = date_local.year
    month_utc = date_local.month
    prefix = f"T{year_utc}{month_utc:02d}"
    count = await get_letter_count(prefix, db)
    number = count + 1

    year_local = date_local.year
    month_local = date_local.month
    day_local = date_local.day

    code = f"T{year_local}{month_local:02d}{day_local:02d}{number:02d}"
    logger.info("Generate letter code process end")
    return code


async def get_letter_stats(current_user: SystemUserWithPermissionsModelOut, db: Session):
    logger.info("Fetch letter status process started")
    status_counts = await get_all_status_counts(current_user, db)
    results = [
        {"status_id": row.id, "status_name": row.name, "count": row.letter_count}
        for row in status_counts
    ]
    logger.info("Fetch letter status process end")
    return results


async def duplicate_letter(letter_id: int, db: Session):
    logger.info("Duplicate letter process started")
    letter_org = await get_active_letter(letter_id, db)
    if not letter_org:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    letter_copy = Letter(
        code=letter_org.code,
        received_datetime=letter_org.received_datetime,
        subject=letter_org.subject,
        other=letter_org.other,
        content=letter_org.content,
        sender=letter_org.sender,
        email=letter_org.email,
        telephone=letter_org.telephone,
        source_id=letter_org.source_id,
        organization_id=letter_org.organization_id,
        status_id=1,
    )
    db.add(letter_copy)
    db.flush()

    folder_path_org = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}")
    folder_path_copy = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_copy.id}")
    attachments_copy = []
    for attachment in letter_org.attachments:
        attachment_copy = LetterAttachment(
            title=attachment.title,
            file_name=duplicate_file(folder_path_org, folder_path_copy, attachment.file_name),
        )
        attachments_copy.append(attachment_copy)
    letter_copy.attachments = attachments_copy
    db.commit()

    logger.info("Duplicate letter process end")
    return {"id": letter_copy.id, "code": letter_copy.code}
