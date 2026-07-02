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
from db.models.models import (Letter, LetterAttachment, LetterAssignee, LetterDepartment,
                               SystemUser, Department, Status, History as HistoryModel)
from exception.exception import NoDataFoundException, CodeExistException, LetterNotFoundException
from models.history import HistoryModelOut
from models.letter import (LetterModelIn, LetterFilter, LetterModelOut, LetterModelOutOne,
                            LetterModelOutList, RemarksModelOut, AttachmentModelOut, IdNameModelOut,
                            LetterExcelFilter)
from models.system_user import SystemUserWithPermissionsModelOut
from service.history import generate_history
from utils.files import validate_files, save_attachment, delete_file, duplicate_file

logger = getLogger(__name__)


async def create_letter(letter_model: LetterModelIn, db: Session) -> Dict:
    if await code_exist(letter_model.code, db):
        raise CodeExistException(f"Letter with code {letter_model.code} is already exist.")

    letter_data = letter_model.model_dump(exclude={'assignee_ids', 'department_ids'})
    letter = Letter(**letter_data)
    letter.status_id = 1
    saved_letter = await save_letter(letter, db)

    for assignee_id in (letter_model.assignee_ids or []):
        db.add(LetterAssignee(letter_id=saved_letter.id, assignee_id=assignee_id))

    for department_id in (letter_model.department_ids or []):
        db.add(LetterDepartment(letter_id=saved_letter.id, department_id=department_id))

    db.commit()
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
        history = [HistoryModelOut.model_validate(h) for h in reversed(letter_db.history)]

    remarks = []
    if 'remark.view' in current_user.permissions:
        remarks = [
            RemarksModelOut(
                id=remark.id,
                content=remark.content,
                subject_no=remark.subject_no,  # NEW
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
        content=None,
        sender=letter_db.sender,
        email=letter_db.email,
        telephone=letter_db.telephone,
        sender_subject_no=letter_db.sender_subject_no,  # NEW
        source=IdNameModelOut.model_validate(letter_db.source) if letter_db.source else None,
        organization=IdNameModelOut.model_validate(letter_db.organization) if letter_db.organization else None,
        remarks=remarks,
        history=history,
        status=IdNameModelOut.model_validate(letter_db.status) if letter_db.status else None,
        status_id=letter_db.status_id,
        related_letters=related_letters,
        attachments=await _make_attachments(letter_db.attachments, letter_id),
        departments=[
            IdNameModelOut(id=ld.department.id, name=ld.department.name)
            for ld in letter_db.departments if ld.department
        ],
        assignees=[
            IdNameModelOut(
                id=la.assignee.id,
                name=f"{la.assignee.first_name} {la.assignee.last_name}"
            )
            for la in letter_db.assignees if la.assignee
        ],
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


async def get_remarks_by_letter_id(letter_id: int, db: Session) -> List[RemarksModelOut]:
    logger.info("Fetch remarks process started")

    letter_db = await get_active_letter(letter_id, db)
    if not letter_db:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found.")

    remarks = [
        RemarksModelOut(
            id=remark.id,
            content=remark.content,
            subject_no=remark.subject_no,  # NEW
            create_datetime=remark.create_datetime,
            department=remark.department,
            status=remark.status,
            assignee=remark.assignee,
            attachments=await _make_remark_attachments(remark.attachments, letter_id, remark.id),
        )
        for remark in reversed(letter_db.remarks) if remark.is_active
    ]

    logger.info("Fetch remarks process end")
    return remarks


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
            status=letter.status.name if letter.status else None,
            organization=letter.organization.name if letter.organization else None,
            department=", ".join([ld.department.name for ld in letter.departments]) if letter.departments else None,
            assignee=", ".join([
                f"{la.assignee.first_name} {la.assignee.last_name}"
                for la in letter.assignees
            ]) if letter.assignees else None,
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

    return {
        'letter_id': updated_letter.id,
        'attribute': attribute,
        'current_id': next_id,
        'previous_id': current_id
    }


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
                if parent == "department":
                    value = ", ".join([
                        getattr(ld.department, child)
                        for ld in obj.departments if ld.department
                    ]) if obj.departments else None
                elif parent == "assignee":
                    value = ", ".join([
                        f"{la.assignee.first_name} {la.assignee.last_name}"
                        for la in obj.assignees if la.assignee
                    ]) if obj.assignees else None
                else:
                    value = getattr(getattr(obj, parent), child) if getattr(obj, parent, None) else None
            elif col_name == "assignee":
                value = ", ".join([
                    f"{la.assignee.first_name} {la.assignee.last_name}"
                    for la in obj.assignees if la.assignee
                ]) if obj.assignees else None
            elif col_name == "attachments":
                value = len(obj.attachments) if obj.attachments else 0
            elif col_name in ["received_datetime", "create_datetime", "update_datetime"]:
                value = getattr(obj, col_name).replace(tzinfo=timezone.utc).astimezone(TIME_ZONE).strftime("%Y-%m-%d")
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

    code = f"T{date_local.year}{date_local.month:02d}{date_local.day:02d}{number:02d}"
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


async def update_letter_assignment(
        letter_id: int,
        status_id: Optional[int],
        department_ids: List[int],
        assignee_ids: List[int],
        db: Session,
        username: str = "System",
        email: str = "",
):
    logger.info("Update letter assignment process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    # ── Status ────────────────────────────────────────────────────────────────
    if status_id and status_id != letter.status_id:
        old_status = letter.status
        new_status = db.query(Status).filter(Status.id == status_id, Status.is_active).first()
        if new_status:
            desc = (
                f"Status changed from {old_status.name} to {new_status.name}"
                if old_status else
                f"Status set to {new_status.name}"
            )
            letter.status_id = status_id
            db.add(HistoryModel(
                description=desc,
                username=username,
                email=email,
                letter_id=letter_id
            ))

    # ── Departments ───────────────────────────────────────────────────────────
    old_dept_ids = {ld.department_id for ld in letter.departments}
    new_dept_ids = set(department_ids)

    if old_dept_ids != new_dept_ids:
        added = new_dept_ids - old_dept_ids
        removed = old_dept_ids - new_dept_ids

        db.query(LetterDepartment).filter(LetterDepartment.letter_id == letter_id).delete()
        for dept_id in department_ids:
            db.add(LetterDepartment(letter_id=letter_id, department_id=dept_id))

        for dept_id in added:
            dept = db.query(Department).filter(Department.id == dept_id).first()
            if dept:
                db.add(HistoryModel(
                    description=f"Department added: {dept.name}",
                    username=username,
                    email=email,
                    letter_id=letter_id
                ))
        for dept_id in removed:
            dept = db.query(Department).filter(Department.id == dept_id).first()
            if dept:
                db.add(HistoryModel(
                    description=f"Department removed: {dept.name}",
                    username=username,
                    email=email,
                    letter_id=letter_id
                ))
    else:
        # No change — still replace to keep data consistent
        db.query(LetterDepartment).filter(LetterDepartment.letter_id == letter_id).delete()
        for dept_id in department_ids:
            db.add(LetterDepartment(letter_id=letter_id, department_id=dept_id))

    # ── Assignees ─────────────────────────────────────────────────────────────
    old_assignee_ids = {la.assignee_id for la in letter.assignees}
    new_assignee_ids = set(assignee_ids)

    if old_assignee_ids != new_assignee_ids:
        added = new_assignee_ids - old_assignee_ids
        removed = old_assignee_ids - new_assignee_ids

        db.query(LetterAssignee).filter(LetterAssignee.letter_id == letter_id).delete()
        for assignee_id in assignee_ids:
            db.add(LetterAssignee(letter_id=letter_id, assignee_id=assignee_id))

        for a_id in added:
            user = db.query(SystemUser).filter(SystemUser.id == a_id).first()
            if user:
                db.add(HistoryModel(
                    description=f"Assignee added: {user.first_name} {user.last_name}",
                    username=username,
                    email=email,
                    letter_id=letter_id
                ))
        for a_id in removed:
            user = db.query(SystemUser).filter(SystemUser.id == a_id).first()
            if user:
                db.add(HistoryModel(
                    description=f"Assignee removed: {user.first_name} {user.last_name}",
                    username=username,
                    email=email,
                    letter_id=letter_id
                ))
    else:
        # No change — still replace to keep data consistent
        db.query(LetterAssignee).filter(LetterAssignee.letter_id == letter_id).delete()
        for assignee_id in assignee_ids:
            db.add(LetterAssignee(letter_id=letter_id, assignee_id=assignee_id))

    db.commit()
    logger.info("Update letter assignment process ended")