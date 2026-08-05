
import os
from datetime import datetime, timezone
from io import BytesIO
from logging import getLogger
from typing import Optional, List, Dict
from utils.email_templates import letter_received_email
from fastapi import UploadFile
from openpyxl.workbook import Workbook
from openpyxl.styles import Font, Alignment  # NEW — for the report heading
from sqlalchemy.orm import Session
from sqlalchemy import func

from config.config import ATTACHMENTS_URL, ATTACHMENTS_DIR, TIME_ZONE
from config.constant import LETTERS_EXCEL_HEADERS
from crud.letter import (save_letter, get_active_letter, update_letter, get_all_letter, code_exist,
                         update_letter_attribute, validate_attribute, letters_excel_data, get_letter_count,
                         get_all_status_counts, get_last_letter_number)
from crud.system_user import get_department_accounts_by_ids  # NEW — resolves department-account ids to SystemUser rows carrying (department_id, department_unit_id)
from db.models.models import (Letter, LetterAttachment, LetterAssignee, LetterDepartment,
                               SystemUser, Department, DepartmentUnit, Status, History as HistoryModel,
                               LetterAssigneeStatus, Remark)
from exception.exception import NoDataFoundException, CodeExistException, LetterNotFoundException, UnauthorizedException
from models.history import HistoryModelOut
from models.letter import (LetterModelIn, LetterFilter, LetterModelOut, LetterModelOutOne,
                            LetterModelOutList, RemarksModelOut, AttachmentModelOut, IdNameModelOut,
                            LetterAssigneeStatusIn, LetterAssigneeStatusOut, AssigneeStatusBrief,
                            LetterExcelFilter)
from models.system_user import SystemUserWithPermissionsModelOut
from service.history import generate_history
from utils.files import validate_files, save_attachment, delete_file, duplicate_file
from crud.organization import get_organization_by_id
from utils.email import send_email
from utils.email_templates import letter_received_email
from exception.exception import ValidationException
from utils.email_templates import letter_received_email
from crud.letter_assignee_status import get_assignee_statuses_by_letter, get_assignee_status, create_assignee_status, delete_assignee_status

logger = getLogger(__name__)

from datetime import datetime, timezone

def _status_days(status_since) -> Optional[int]:
    if not status_since:
        return None
    since = status_since if status_since.tzinfo else status_since.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - since).days


def _days_pending(
        received_datetime,
        status_name: Optional[str],
        status_since,
        assignee_status_rows: Optional[List] = None,
) -> Optional[int]:
    """
    Days since the letter was received. Keeps counting from the original
    received_datetime — EXCEPT once the letter is considered "done", at
    which point it freezes instead of climbing forever.

    CHANGED — "done" now depends on assignee-level completion when the
    letter HAS assignees: it only freezes once EVERY assignee's own status
    is "Completed", freezing at the moment the LAST one completed (not the
    letter's overall status, which per-assignee statuses don't keep in
    sync). Letters with no assignees fall back to the old rule: frozen once
    the letter's own overall status is "Completed".
    """
    if not received_datetime:
        return None
    received = received_datetime if received_datetime.tzinfo else received_datetime.replace(tzinfo=timezone.utc)

    if assignee_status_rows:
        all_completed = all(
            (row.status.name == "Completed") if row.status else False
            for row in assignee_status_rows
        )
        if all_completed:
            completion_times = [
                (row.status_since if row.status_since.tzinfo else row.status_since.replace(tzinfo=timezone.utc))
                for row in assignee_status_rows if row.status_since
            ]
            end = max(completion_times) if completion_times else datetime.now(timezone.utc)
        else:
            end = datetime.now(timezone.utc)
    else:
        if status_name == "Completed" and status_since:
            end = status_since if status_since.tzinfo else status_since.replace(tzinfo=timezone.utc)
        else:
            end = datetime.now(timezone.utc)

    return (end - received).days


def _department_label(ld: "LetterDepartment") -> str:
    """
    CHANGED — small shared helper: prefer the sub-unit's name if this
    department entry was routed to a specific unit, otherwise fall back to
    the parent department's name. Used everywhere a LetterDepartment row is
    turned into display text, so the "shows section name instead of unit
    name" bug can't reappear in one place but not another.
    """
    if ld.department_unit:
        return ld.department_unit.name
    return ld.department.name if ld.department else "Unknown"


async def create_letter(letter_model: LetterModelIn, db: Session) -> Dict:
    if await code_exist(letter_model.code, db):
        raise CodeExistException(f"Letter with code {letter_model.code} is already exist.")

    letter_data = letter_model.model_dump(exclude={'assignee_ids', 'department_ids'})
    letter = Letter(**letter_data)
    letter.status_id = 1
    saved_letter = await save_letter(letter, db)

    for assignee_id in (letter_model.assignee_ids or []):
        db.add(LetterAssignee(letter_id=saved_letter.id, assignee_id=assignee_id))

    # NEW — give every assignee attached at CREATION time their own
    # per-assignee status row too. Previously this only happened inside
    # update_letter_assignment for assignees added during a later edit
    # (added = new_ids - old_ids), so a letter created with an assignee
    # already on it (e.g. via the "Insert Letter" form) got a LetterAssignee
    # row but no matching LetterAssigneeStatus row — the assignee showed up
    # under "Assignees" but had nothing in "Assignee Statuses" and nothing
    # to update.
    for assignee_id in (letter_model.assignee_ids or []):
        db.add(LetterAssigneeStatus(
            letter_id=saved_letter.id,
            assignee_id=assignee_id,
            status_id=letter.status_id,
            status_since=datetime.utcnow(),
        ))

    # CHANGED — `department_ids` now carries department ACCOUNT ids
    # (system_user.id of an is_department_account=True row), not raw
    # Department.id. Each account already knows its own department_id and
    # (optionally) department_unit_id, so we resolve those here and store
    # both on the LetterDepartment row. This is what lets a letter be routed
    # to a specific sub-unit (e.g. "Banking Regulation and Statistic Unit")
    # instead of always collapsing to the parent section.
    dept_accounts = await get_department_accounts_by_ids(letter_model.department_ids or [], db)
    for account in dept_accounts:
        db.add(LetterDepartment(
            letter_id=saved_letter.id,
            department_id=account.department_id,
            department_unit_id=account.department_unit_id,  # NEW
        ))

    db.commit()

    # NEW — notify the organization by email that their letter was received,
    # if an organization is linked and has an email on file
    if letter_model.organization_id:
        organization = await get_organization_by_id(letter_model.organization_id, db)
        if organization and organization.email:
            email_subject, email_body = letter_received_email(
                organization_name=organization.name,
                letter_code=saved_letter.code,
                subject=saved_letter.subject or "",
                received_datetime=saved_letter.received_datetime,
            )
            await send_email(organization.email, email_subject, email_body)

    # CHANGED — notify each routed department/unit's email, using the
    # already-resolved dept_accounts (also fixes the previous dead code
    # after `return`, and the undefined `get_department_by_id` call).
    for account in dept_accounts:
        notify_email = (
            account.department_unit.email
            if account.department_unit and account.department_unit.email
            else (account.department.email if account.department else None)
        )
        if notify_email:
            email_subject, email_body = letter_received_email(
                organization_name=_department_label_for_account(account),
                letter_code=saved_letter.code,
                subject=saved_letter.subject or "",
                received_datetime=saved_letter.received_datetime,
            )
            await send_email(notify_email, email_subject, email_body)

    return {'id': saved_letter.id, 'code': saved_letter.code}


def _department_label_for_account(account: SystemUser) -> str:
    if account.department_unit:
        return account.department_unit.name
    return account.department.name if account.department else "Unknown"


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
                subject_no=remark.subject_no,
                create_datetime=remark.create_datetime,
                department=remark.department,
                status=remark.status,
                assignee=remark.assignee,
                created_by=remark.created_by_name,
                attachments=await _make_remark_attachments(remark.attachments, letter_id, remark.id),
            )
            for remark in reversed(letter_db.remarks) if remark.is_active
        ]

    # NEW — self-heal: any assignee currently on the letter (LetterAssignee)
    # who doesn't yet have a matching LetterAssigneeStatus row gets one
    # created here, defaulting to the letter's current overall status. This
    # covers letters created before this feature existed, and any future
    # gap where an assignee ends up without a status row — the panel will
    # never silently show nothing for someone who is actually assigned.
    existing_status_assignee_ids = {row.assignee_id for row in letter_db.assignee_statuses}
    missing_rows = False
    for la in letter_db.assignees:
        if la.assignee_id not in existing_status_assignee_ids:
            db.add(LetterAssigneeStatus(
                letter_id=letter_id,
                assignee_id=la.assignee_id,
                status_id=letter_db.status_id,
                status_since=letter_db.status_since or datetime.utcnow(),
            ))
            missing_rows = True
    if missing_rows:
        db.commit()

    # CHANGED — moved above `letter_response` construction. This block
    # was previously placed *after* letter_response was built while still
    # being referenced inside it, which raised
    #   NameError: name 'assignee_statuses_out' is not defined
    # on every single call to get_letter_by_id.
    assignee_status_rows = await get_assignee_statuses_by_letter(letter_id, db)
    assignee_statuses_out = [
        LetterAssigneeStatusOut(
            assignee_id=row.assignee_id,
            assignee_name=f"{row.assignee.first_name} {row.assignee.last_name}" if row.assignee else "Unknown",
            status_id=row.status_id,
            status_name=row.status.name if row.status else "Unknown",
            file_name=row.file_name,
            status_since=row.status_since,
            status_days=_status_days(row.status_since),
            can_edit=(current_user.id == row.assignee_id),  # only true for the logged-in user's own row
        )
        for row in assignee_status_rows
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
        sender_subject_no=letter_db.sender_subject_no,
        registered_post_no=letter_db.registered_post_no,
        source=IdNameModelOut.model_validate(letter_db.source) if letter_db.source else None,
        organization=IdNameModelOut.model_validate(letter_db.organization) if letter_db.organization else None,
        remarks=remarks,
        history=history,
        status=IdNameModelOut.model_validate(letter_db.status) if letter_db.status else None,
        status_id=letter_db.status_id,
        status_since=letter_db.status_since,
        status_days=_status_days(letter_db.status_since),
        assignee_statuses=assignee_statuses_out,
        related_letters=related_letters,
        attachments=await _make_attachments(letter_db.attachments, letter_id),
        # CHANGED — id/name now come from the sub-unit if one was set on
        # this LetterDepartment row, falling back to the parent department.
        # This is what the frontend badge/checklist labels actually render.
        departments=[
            IdNameModelOut(
                id=ld.department_unit.id if ld.department_unit else ld.department.id,
                name=_department_label(ld)
            )
            for ld in letter_db.departments if ld.department
        ],
        assignees=[
            IdNameModelOut(
                id=la.assignee.id,
                name=f"{la.assignee.first_name} {la.assignee.last_name}"
            )
            for la in letter_db.assignees if la.assignee
        ],
        recommended_to=(
            IdNameModelOut(
                id=letter_db.recommended_to.id,
                name=f"{letter_db.recommended_to.first_name} {letter_db.recommended_to.last_name}"
            )
            if getattr(letter_db, "recommended_to", None) else None
        ),
        forwarded_to=(
            IdNameModelOut(
                id=letter_db.forwarded_to.id,
                name=f"{letter_db.forwarded_to.first_name} {letter_db.forwarded_to.last_name}"
            )
            if getattr(letter_db, "forwarded_to", None) else None
        ),
        completion_file_name=letter_db.completion_file_name,
        cheque_deposited=letter_db.cheque_deposited or False,
        cheque_deposit_date=letter_db.cheque_deposit_date,
        cheque_account_no=letter_db.cheque_account_no,
        cheque_bank=letter_db.cheque_bank,
        cheque_branch=letter_db.cheque_branch,
        remarks_count=sum(1 for r in letter_db.remarks if r.is_active),  # NEW
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
            url=f"{ATTACHMENTS_URL}/letter_{letter_id}/{attachment.file_name}",
            file_size=attachment.file_size,
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
            url=f"{ATTACHMENTS_URL}/letter_{letter_id}/remark_{remark_id}/{attachment.file_name}",
            file_size=attachment.file_size,
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
            subject_no=remark.subject_no,
            create_datetime=remark.create_datetime,
            department=remark.department,
            status=remark.status,
            assignee=remark.assignee,
            created_by=remark.created_by_name,
            attachments=await _make_remark_attachments(remark.attachments, letter_id, remark.id),
        )
        for remark in reversed(letter_db.remarks) if remark.is_active
    ]

    logger.info("Fetch remarks process end")
    return remarks


async def update_letter_by_id(
        letter_id: int,
        letter_model: LetterModelIn,
        db: Session,
        current_user: SystemUserWithPermissionsModelOut,
) -> LetterModelOut:
    logger.info("Update letter process started")

    letter_db = await get_active_letter(letter_id, db)
    if not letter_db:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    if letter_model.code != letter_db.code and await code_exist(letter_model.code, db):
        raise CodeExistException(f"Letter with code {letter_model.code} is already exist")

    updated_letter = letter_model.model_dump(exclude={'assignee_ids', 'department_ids'})

    changed_fields = []
    for field, value in updated_letter.items():
        old_value = getattr(letter_db, field, None)
        if str(old_value) != str(value):
            changed_fields.append(field)
        setattr(letter_db, field, value)

    if changed_fields:
        db.add(HistoryModel(
            description="Letter details updated (" + ", ".join(changed_fields) + ")",
            username=f"{current_user.first_name} {current_user.last_name}",
            email=current_user.email,
            letter_id=letter_id,
        ))

    saved_letter = await update_letter(letter_db, db)
    letter_response = LetterModelOut.model_validate(saved_letter)

    logger.info("Update letter process ended")
    return letter_response
async def _resolve_dept_account_ids(letter_departments, db: Session) -> List[int]:
    if not letter_departments:
        return []
    pairs = [(ld.department_id, ld.department_unit_id) for ld in letter_departments]
    accounts = db.query(SystemUser).filter(
        SystemUser.is_department_account == True,
        SystemUser.department_id.in_([p[0] for p in pairs]),
    ).all()
    result = []
    for dept_id, unit_id in pairs:
        for acc in accounts:
            if acc.department_id == dept_id and acc.department_unit_id == unit_id:
                result.append(acc.id)
                break
    return result

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

    # NEW — bulk-fetch per-assignee statuses for every letter on this page in
    # ONE query instead of one query per letter (N+1), then group them by
    # letter_id in Python for the loop below. We keep the raw rows (not just
    # display strings) so _days_pending can check per-assignee completion,
    # and so the structured AssigneeStatusBrief objects can carry each
    # assignee's own file_name alongside their status.
    letter_ids_on_page = [letter.id for letter in letters_db]
    status_rows_by_letter: Dict[int, List] = {}
    if letter_ids_on_page:
        rows = db.query(LetterAssigneeStatus).filter(
            LetterAssigneeStatus.letter_id.in_(letter_ids_on_page)
        ).all()
        for row in rows:
            status_rows_by_letter.setdefault(row.letter_id, []).append(row)

    # NEW — bulk remark counts (one query for the whole page), so the
    # dashboard's Actions column can show a "N remarks" notify badge
    # without an N+1 query per row.
    remarks_count_by_letter: Dict[int, int] = {}
    if letter_ids_on_page:
        count_rows = db.query(Remark.letter_id, func.count(Remark.id)).filter(
            Remark.letter_id.in_(letter_ids_on_page),
            Remark.is_active == True,
        ).group_by(Remark.letter_id).all()
        remarks_count_by_letter = {letter_id: count for letter_id, count in count_rows}

    letters_response = [
        LetterModelOutList(
            id=letter.id,
            code=letter.code,
            create_datetime=letter.received_datetime,
            subject=letter.subject,
            status=letter.status.name if letter.status else None,
            status_since=letter.status_since,
            status_days=_status_days(letter.status_since),
            days_pending=_days_pending(
                letter.received_datetime,
                letter.status.name if letter.status else None,
                letter.status_since,
                status_rows_by_letter.get(letter.id, []),  # CHANGED — considers per-assignee completion
            ),
            organization=letter.organization.name if letter.organization else None,
            # CHANGED — show the sub-unit name where one is set, not the
            # parent section name
            department=", ".join([_department_label(ld) for ld in letter.departments]) if letter.departments else None,
            department_account_ids=await _resolve_dept_account_ids(letter.departments, db),
            assignee=", ".join([
                f"{la.assignee.first_name} {la.assignee.last_name}"
                for la in letter.assignees
            ]) if letter.assignees else None,
            # NEW — actual ids, not just the display string, so the Quick
            # Edit dialog on the dashboard can preselect who's already
            # assigned instead of opening with an empty checklist every time.
            assignee_ids=[la.assignee_id for la in letter.assignees],
            other=letter.other,
            sender_subject_no=letter.sender_subject_no,
            forwarded_to=(
                f"{letter.forwarded_to.first_name} {letter.forwarded_to.last_name}"
                if getattr(letter, "forwarded_to", None) else None
            ),
            completion_file_name=letter.completion_file_name,
            cheque_deposited=letter.cheque_deposited or False,  # NEW
            cheque_deposit_date=letter.cheque_deposit_date,  # NEW
            cheque_account_no=letter.cheque_account_no,  # NEW
            cheque_bank=letter.cheque_bank,  # NEW
            cheque_branch=letter.cheque_branch,  # NEW
            # CHANGED — structured objects instead of flat "Name: Status"
            # strings, so the frontend can color each badge by its own
            # status and show each assignee's own file_name in the File
            # Name column.
            assignee_statuses=[
                AssigneeStatusBrief(
                    assignee_name=f"{row.assignee.first_name} {row.assignee.last_name}" if row.assignee else "Unknown",
                    status_name=row.status.name if row.status else "Unknown",
                    file_name=row.file_name,
                )
                for row in status_rows_by_letter.get(letter.id, [])
            ],
            remarks_count=remarks_count_by_letter.get(letter.id, 0),  # NEW
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
        saved_file_name, size = save_attachment(file, folder_path)
        db.add(LetterAttachment(
            letter_id=letter_id,
            title=file.filename,
            file_name=saved_file_name,
            file_size=size,
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
        filename, size = save_attachment(file, folder_path)
        db.add(LetterAttachment(
            letter_id=letter_id,
            title=file.filename,
            file_name=filename,
            file_size=size,
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

    if attribute == "status" and current_user.allowed_status_ids:
        if next_id not in current_user.allowed_status_ids:
            raise NoDataFoundException("This role is not permitted to set letters to this status")

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

    num_cols = max(len(selected_headers), 1)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    heading_cell = ws.cell(row=1, column=1, value="Department of Cooperative Development")
    heading_cell.font = Font(bold=True, size=14)
    heading_cell.alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
    subheading_cell = ws.cell(row=2, column=1, value="COOP PMS - Letters Report")
    subheading_cell.font = Font(italic=True, size=11)
    subheading_cell.alignment = Alignment(horizontal="center")

    header_row_index = 4
    ws.append([])  # row 3 — blank spacer
    ws.append([h[0] for h in selected_headers])  # row 4 — column headers

    for obj in rows:
        row_data = []
        for _, col_name in selected_headers:
            if "." in col_name:
                parent, child = col_name.split(".")
                if parent == "department":
                    # CHANGED — sub-unit name where set, else parent department
                    value = ", ".join([
                        _department_label(ld)
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
            elif col_name == "cheque_details":
                # NEW — combined single column instead of 5 separate ones
                # (deposited / date / account / bank / branch). Only makes
                # sense when there's a cheque number on the letter at all.
                if not obj.other:
                    value = None
                elif not obj.cheque_deposited:
                    value = "Not deposited"
                else:
                    parts = ["Deposited"]
                    if obj.cheque_deposit_date:
                        parts.append(obj.cheque_deposit_date.replace(tzinfo=timezone.utc).astimezone(TIME_ZONE).strftime("%Y-%m-%d"))
                    if obj.cheque_bank:
                        bank_part = obj.cheque_bank
                        if obj.cheque_branch:
                            bank_part += f" ({obj.cheque_branch})"
                        parts.append(bank_part)
                    if obj.cheque_account_no:
                        parts.append(f"A/C {obj.cheque_account_no}")
                    value = " · ".join(parts)
            elif col_name in ["received_datetime", "create_datetime", "update_datetime"]:
                value = getattr(obj, col_name).replace(tzinfo=timezone.utc).astimezone(TIME_ZONE).strftime("%Y-%m-%d")
            else:
                value = getattr(obj, col_name)
            row_data.append(value)
        ws.append(row_data)

    ws.print_title_rows = f'1:{header_row_index}'

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    logger.info("Excel generation process end")
    return output


async def generate_letter_code(datetime_utc: datetime, db: Session) -> str:
    logger.info("Generate letter code process started")

    date_local = datetime_utc.astimezone(TIME_ZONE)
    month_prefix = f"T{date_local.year}{date_local.month:02d}"
    day_str = f"{date_local.day:02d}"

    last_number = await get_last_letter_number(month_prefix, db)
    number = last_number + 1

    code = f"{month_prefix}{day_str}{number:02d}"
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
            file_size=attachment.file_size,
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
        allowed_status_ids: Optional[List[int]] = None,
        allowed_department_ids=None,
        allowed_assignee_role_ids=None,
        can_change_status: bool = True,
        can_change_department: bool = True,
        can_assign: bool = True,
        file_name: Optional[str] = None,
        recommended_to_id: Optional[int] = None,
        can_forward: bool = True,
        forwarded_to_id: Optional[int] = None,
):
    logger.info("Update letter assignment process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    if can_change_status and status_id and status_id != letter.status_id:
        if allowed_status_ids:
            if status_id not in allowed_status_ids:
                raise NoDataFoundException("This role is not permitted to set letters to this status")

        old_status = letter.status
        new_status = db.query(Status).filter(Status.id == status_id, Status.is_active).first()
        if new_status:
            if new_status.requires_file_name:
                if not file_name or not file_name.strip():
                    raise ValidationException(f"File Name is required when setting status to '{new_status.name}'")
                letter.completion_file_name = file_name.strip()

            desc = (
                f"Status changed from {old_status.name} to {new_status.name}" if old_status else f"Status set to {new_status.name}")
            letter.status_id = status_id
            letter.status_since = datetime.utcnow()
            db.add(HistoryModel(description=desc, username=username, email=email, letter_id=letter_id))

    # ── Departments ───────────────────────────────────────────────────────────
    # CHANGED — `department_ids` are department ACCOUNT ids (system_user.id
    # of is_department_account=True rows), not raw Department.id. We resolve
    # each account to its (department_id, department_unit_id) pair and store
    # both on LetterDepartment, so a letter routed to a sub-unit account
    # (e.g. "Banking Regulation and Statistic Unit") stays scoped to that
    # unit instead of collapsing to the parent section. Comparison/dedup is
    # done on the (department_id, department_unit_id) pair, not on
    # department_id alone — two different sub-unit accounts under the same
    # section must be distinguishable.
    if can_change_department:
        dept_accounts = await get_department_accounts_by_ids(department_ids, db)

        if allowed_department_ids:
            disallowed = {a.department_id for a in dept_accounts} - set(allowed_department_ids)
            if disallowed:
                raise NoDataFoundException(
                    "This role is not permitted to assign letters to one or more of the selected departments")

        old_pairs = {(ld.department_id, ld.department_unit_id) for ld in letter.departments}
        new_pairs = {(a.department_id, a.department_unit_id) for a in dept_accounts}

        if old_pairs != new_pairs:
            added_accounts = [a for a in dept_accounts if (a.department_id, a.department_unit_id) not in old_pairs]
            removed_pairs = old_pairs - new_pairs

            db.query(LetterDepartment).filter(LetterDepartment.letter_id == letter_id).delete()
            for account in dept_accounts:
                db.add(LetterDepartment(
                    letter_id=letter_id,
                    department_id=account.department_id,
                    department_unit_id=account.department_unit_id,
                ))

            for account in added_accounts:
                label = _department_label_for_account(account)
                db.add(HistoryModel(
                    description=f"Department added: {label}",
                    username=username, email=email, letter_id=letter_id
                ))
                notify_email = (
                    account.department_unit.email
                    if account.department_unit and account.department_unit.email
                    else (account.department.email if account.department else None)
                )
                if notify_email:
                    email_subject, email_body = letter_received_email(
                        organization_name=label,
                        letter_code=letter.code,
                        subject=letter.subject or "",
                        received_datetime=letter.received_datetime,
                    )
                    await send_email(notify_email, email_subject, email_body)

            for dept_id, unit_id in removed_pairs:
                dept = db.query(Department).filter(Department.id == dept_id).first()
                unit = db.query(DepartmentUnit).filter(DepartmentUnit.id == unit_id).first() if unit_id else None
                label = unit.name if unit else (dept.name if dept else "Unknown")
                db.add(HistoryModel(
                    description=f"Department removed: {label}",
                    username=username,
                    email=email,
                    letter_id=letter_id
                ))
        else:
            db.query(LetterDepartment).filter(LetterDepartment.letter_id == letter_id).delete()
            for account in dept_accounts:
                db.add(LetterDepartment(
                    letter_id=letter_id,
                    department_id=account.department_id,
                    department_unit_id=account.department_unit_id,
                ))

    # ── Assignees ─────────────────────────────────────────────────────────────
    if can_assign:
        old_assignee_ids = {la.assignee_id for la in letter.assignees}
        new_assignee_ids = set(assignee_ids)

        if old_assignee_ids != new_assignee_ids:
            added = new_assignee_ids - old_assignee_ids
            removed = old_assignee_ids - new_assignee_ids

            db.query(LetterAssignee).filter(LetterAssignee.letter_id == letter_id).delete()
            for assignee_id in assignee_ids:
                db.add(LetterAssignee(letter_id=letter_id, assignee_id=assignee_id))

            # NEW — give each newly-added assignee their own status row, defaulting to the letter's current status
            for a_id in added:
                existing = await get_assignee_status(letter_id, a_id, db)
                if not existing:
                    from db.models.models import LetterAssigneeStatus
                    db.add(LetterAssigneeStatus(
                        letter_id=letter_id,
                        assignee_id=a_id,
                        status_id=letter.status_id,
                        status_since=datetime.utcnow(),
                    ))

            # NEW — clean up status rows for assignees who were removed
            for a_id in removed:
                await delete_assignee_status(letter_id, a_id, db)

            for a_id in added:
                user = db.query(SystemUser).filter(SystemUser.id == a_id).first()
                if user:
                    db.add(HistoryModel(
                        description=f"Assignee added: {user.first_name} {user.last_name}",
                        username=username, email=email, letter_id=letter_id
                    ))
            for a_id in removed:
                user = db.query(SystemUser).filter(SystemUser.id == a_id).first()
                if user:
                    db.add(HistoryModel(
                        description=f"Assignee removed: {user.first_name} {user.last_name}",
                        username=username, email=email, letter_id=letter_id
                    ))
        else:
            db.query(LetterAssignee).filter(LetterAssignee.letter_id == letter_id).delete()
            for assignee_id in assignee_ids:
                db.add(LetterAssignee(letter_id=letter_id, assignee_id=assignee_id))

    # ── Recommended To ───────────────────────────────────────────────────────
    # CHANGED — was `if can_assign and recommended_to_id is not None:`, which
    # meant unchecking "Send to Recommendation" on the frontend (which sends
    # an explicit `recommended_to_id: null`) could never actually clear the
    # field, because `None` from an explicit null is indistinguishable from
    # `None` as "not provided". The permission check now happens only when a
    # real id is being set; clearing (None) always goes through.
    if can_assign:
        if recommended_to_id is not None and allowed_assignee_role_ids:
            target_user = db.query(SystemUser).filter(SystemUser.id == recommended_to_id).first()
            if target_user and target_user.role_id not in allowed_assignee_role_ids:
                raise NoDataFoundException(
                    "This role is not permitted to recommend letters to this user")

        if letter.recommended_to_id != recommended_to_id:
            new_target = db.query(SystemUser).filter(SystemUser.id == recommended_to_id).first() if recommended_to_id else None
            old_target = db.query(SystemUser).filter(SystemUser.id == letter.recommended_to_id).first() if letter.recommended_to_id else None
            letter.recommended_to_id = recommended_to_id
            if new_target:
                db.add(HistoryModel(
                    description=f"Recommended to: {new_target.first_name} {new_target.last_name}",
                    username=username,
                    email=email,
                    letter_id=letter_id,
                ))
            elif old_target:
                db.add(HistoryModel(
                    description=f"Recommendation to {old_target.first_name} {old_target.last_name} removed",
                    username=username,
                    email=email,
                    letter_id=letter_id,
                ))

    # ── Forwarded To ─────────────────────────────────────────────────────────
    # NEW — entirely separate from Assignees AND from Recommended To: no
    # status is required or changed by forwarding, and forwarding never
    # touches who the letter is actually assigned to or recommended to.
    # `Letter.forwarded_to_id` is also included in the visibility conditions
    # in crud/letter.py, so the person a letter is forwarded to can actually
    # see it in their letters list — not just in this letter's detail view.
    if can_forward:
        if letter.forwarded_to_id != forwarded_to_id:
            new_target = db.query(SystemUser).filter(SystemUser.id == forwarded_to_id).first() if forwarded_to_id else None
            old_target = db.query(SystemUser).filter(SystemUser.id == letter.forwarded_to_id).first() if letter.forwarded_to_id else None
            letter.forwarded_to_id = forwarded_to_id
            if new_target:
                db.add(HistoryModel(
                    description=f"Forwarded to: {new_target.first_name} {new_target.last_name}",
                    username=username,
                    email=email,
                    letter_id=letter_id,
                ))
            elif old_target:
                db.add(HistoryModel(
                    description=f"Forward to {old_target.first_name} {old_target.last_name} removed",
                    username=username,
                    email=email,
                    letter_id=letter_id,
                ))

    db.commit()
    logger.info("Update letter assignment process ended")


async def update_cheque_deposit(letter_id: int, payload: "ChequeDepositIn", db: Session, current_user) -> None:
    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    if not letter.other:
        raise ValidationException("This letter has no Cheque/Money Order number on file")

    letter.cheque_deposited = payload.deposited
    letter.cheque_deposit_date = payload.deposit_date if payload.deposited else None
    letter.cheque_account_no = payload.account_no if payload.deposited else None
    letter.cheque_bank = payload.bank if payload.deposited else None
    letter.cheque_branch = payload.branch if payload.deposited else None

    db.add(HistoryModel(
        description=f"Cheque {'marked as deposited' if payload.deposited else 'deposit unmarked'}",
        username=f"{current_user.first_name} {current_user.last_name}",
        email=current_user.email,
        letter_id=letter_id,
    ))
    db.commit()

async def update_assignee_status(
        letter_id: int,
        assignee_id: int,
        payload: LetterAssigneeStatusIn,
        db: Session,
        current_user,
):
    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise NoDataFoundException(f"Letter with ID {letter_id} not found")

    # NEW — only the assignee themselves may edit their own status entry
    if current_user.id != assignee_id:
        raise UnauthorizedException("You can only update your own assigned status")

    row = await get_assignee_status(letter_id, assignee_id, db)
    if not row:
        raise NoDataFoundException("You are not assigned to this letter")

    if getattr(current_user, "allowed_status_ids", None):
        if payload.status_id not in current_user.allowed_status_ids:
            raise NoDataFoundException("This role is not permitted to set letters to this status")

    new_status = db.query(Status).filter(Status.id == payload.status_id, Status.is_active).first()
    if not new_status:
        raise NoDataFoundException("Status not found")

    if new_status.requires_file_name:
        if not payload.file_name or not payload.file_name.strip():
            raise ValidationException(f"File Name is required when setting status to '{new_status.name}'")

    old_status_name = row.status.name if row.status else "Unknown"
    row.status_id = payload.status_id
    row.file_name = payload.file_name.strip() if payload.file_name else None
    if row.status_id != payload.status_id:
        row.status_since = datetime.utcnow()

    db.add(HistoryModel(
        description=f"{current_user.first_name} {current_user.last_name}'s status changed from {old_status_name} to {new_status.name}",
        username=f"{current_user.first_name} {current_user.last_name}",
        email=current_user.email,
        letter_id=letter_id,
    ))
    db.commit()