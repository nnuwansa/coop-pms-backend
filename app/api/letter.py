


import logging
from datetime import datetime
from math import ceil
from typing import Optional, List

from fastapi import APIRouter, Path, UploadFile, Depends, Body
from fastapi.params import Form, File
from starlette.responses import StreamingResponse
from pydantic import BaseModel

from db.session import DbSession
from db.models.models import History as HistoryModel
from exception.exception import UnauthorizedException
from models.letter import (
    LetterModelIn,
    LetterFilter, SwitchAttributeType, SwitchLetterAttribute, LetterExcelFilter,
    RemarkUpdateIn, RemarkDeleteIn, RemarkHistoryModelOut,
)
from models.history import HistoryModelOut
from models.response import GenericResponse, GenericResponsePaginated
from models.system_user import SystemUserWithPermissionsModelOut
from service.letter import (
    create_letter,
    get_letter_by_id,
    delete_letter_by_id,
    update_letter_by_id,
    get_remarks_by_letter_id,
    get_list_letters,
    bind_letter_attachment,
    update_letter_attachments,
    switch_letter_attribute,
    letters_excel,
    generate_letter_code,
    get_letter_stats,
    duplicate_letter,
    get_deleted_letters_service,
    restore_letter_service,
    permanently_delete_letter_service,
    update_letter_assignment as _update_assignment,
)
from service.remark import (
    create_remarks_and_attachments, update_remark_and_attachments,
    delete_remark_by_id, bind_remark_attachments, get_remark_history,
)
from utils.auth import get_current_user, has_permission
from models.letter import ChequeDepositIn
from service.letter import update_cheque_deposit as _update_cheque_deposit
from models.letter import LetterAssigneeStatusIn
from service.letter import update_assignee_status as _update_assignee_status
from service.letter import assign_initials_by as _assign_initials_by
from service.letter import confirm_initials_by as _confirm_initials_by
from service.letter import bulk_confirm_initials_by as _bulk_confirm

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/letter",
    tags=["Letter"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=GenericResponse)
async def create_letter_api(
        letter: LetterModelIn,
        db: DbSession, current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("letter.create"))
):
    logger.debug(f"Request to create letter: {letter}")
    letter_obj = await create_letter(letter, db, current_user_id=current_user.id)
    return GenericResponse(data=letter_obj, message="Letter created successfully")


@router.get("/{letter_id}", response_model=GenericResponse)
async def get_letter_by_id_api(
        db: DbSession,
        letter_id: int = Path(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    logger.debug(f"Request to fetch letter with ID: {letter_id}")
    result = await get_letter_by_id(letter_id, current_user, db)
    return GenericResponse(data=result, message="Letter fetched successfully")


@router.put("/{letter_id}", response_model=GenericResponse)
async def update_letter_by_id_api(
        letter_model: LetterModelIn,
        db: DbSession,
        _=Depends(has_permission("letter.update")),
        letter_id: int = Path(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    logger.debug(f"Request to update letter ID {letter_id} with data: {letter_model}")
    result = await update_letter_by_id(letter_id, letter_model, db, current_user)
    return GenericResponse(data=result, message=f"Letter {result.code} has been successfully updated")


@router.post("/list", response_model=GenericResponsePaginated)
async def get_letters_api(
        db: DbSession,
        filters: Optional[LetterFilter] = None,
        page: int = 1,
        page_size: int = 10,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    logger.debug(f"Request to list letters with filters: {filters}")
    total, result = await get_list_letters(filters, page, page_size, current_user, db)
    total_pages = ceil(total / page_size) if page_size else 1
    return GenericResponsePaginated(data=result, message="Letters fetched successfully",
                                    total=total,
                                    total_pages=total_pages,
                                    page=page, page_size=page_size)


@router.delete("/{letter_id}", response_model=GenericResponse)
async def delete_letter_by_id_api(
        db: DbSession,
        _=Depends(has_permission("letter.delete")),
        letter_id: int = Path(...)
):
    logger.debug(f"Request to delete letter with ID: {letter_id}")
    await delete_letter_by_id(letter_id, db)
    return GenericResponse(message='Letter deleted successfully')


class RemarkIn(BaseModel):
    content: str
    subject_no: Optional[str] = None


@router.post("/{letter_id}/remarks", response_model=GenericResponse)
async def add_remark_api(
        db: DbSession,
        letter_id: int,
        remark_in: RemarkIn = Body(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("remark.create"))
):
    remark_id = await create_remarks_and_attachments(
        letter_id, [], remark_in.content, db, current_user, subject_no=remark_in.subject_no
    )
    return GenericResponse(data={"id": remark_id}, message="Remark created successfully")


@router.get("/{letter_id}/remarks", response_model=GenericResponse)
async def list_remarks_api(
        db: DbSession,
        letter_id: int = Path(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    remarks = await get_remarks_by_letter_id(letter_id, db)
    return GenericResponse(data=remarks, message="Remarks fetched successfully")


@router.put("/remark/{remark_id}", response_model=GenericResponse)
async def update_remark(
        db: DbSession,
        remark_id: int,
        payload: RemarkUpdateIn,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("remark.update"))
):
    logger.debug(f"Request to update remark ID: {remark_id}")
    await update_remark_and_attachments(
        remark_id, payload.content, payload.reason, db, current_user,
        subject_no=payload.subject_no,
    )
    return GenericResponse(message="Remark updated successfully")


@router.post("/{letter_id}/remarks/{remark_id}/attachments", response_model=GenericResponse)
async def add_remark_attachments_api(
        db: DbSession,
        letter_id: int,
        remark_id: int,
        attachments: Optional[List[UploadFile]] = File(default=None),
        _=Depends(has_permission("remark.create"))
):
    attachments = attachments or []
    filenames = await bind_remark_attachments(letter_id, remark_id, attachments, db)
    return GenericResponse(data={"filenames": filenames}, message="Remark attachments bound successfully")


@router.delete("/remark/{remark_id}", response_model=GenericResponse)
async def delete_remark_by_id_api(
        db: DbSession,
        payload: RemarkDeleteIn,
        remark_id: int = Path(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("remark.delete"))
):
    logger.debug(f"Request to delete remark with ID: {remark_id}")
    await delete_remark_by_id(remark_id, payload.reason, db, current_user)
    return GenericResponse(message='Remark deleted successfully')


@router.get("/{letter_id}/remarks/history", response_model=GenericResponse)
async def get_remark_history_api(
        db: DbSession,
        letter_id: int = Path(...),
        _: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    logger.debug(f"Request to fetch remark history for letter ID: {letter_id}")
    history = await get_remark_history(letter_id, db)
    result = [RemarkHistoryModelOut.model_validate(h) for h in history]
    return GenericResponse(data=result, message="Remark history fetched successfully")


@router.post("/{letter_id}/attachments", response_model=GenericResponse)
async def add_letter_attachments(
        db: DbSession,
        letter_id: int,
        attachments: Optional[List[UploadFile]] = File(default=None),
        _=Depends(has_permission("letter.create"))
):
    logger.debug(f"Request to bind attachments with ID: {letter_id}")
    attachments = attachments or []
    filenames = await bind_letter_attachment(letter_id, attachments, db)
    return GenericResponse(data={"filenames": filenames}, message="Letter-attachments binds successfully")


@router.put("/{letter_id}/attachments")
async def update_attachments(
        db: DbSession,
        letter_id: int,
        attachments: Optional[List[UploadFile]] = File(default=None),
        _=Depends(has_permission("letter.update"))
):
    logger.debug(f"Request to update attachments for letter ID: {letter_id}")

    attachments = attachments or []
    updated_filenames = await update_letter_attachments(letter_id, attachments, db)

    return GenericResponse(
        data={"attachment_filenames": updated_filenames},
        message="Attachments updated successfully"
    )
class BulkConfirmInitialsByIn(BaseModel):
    letter_ids: List[int]
    notes: Optional[str] = None


@router.put("/initials-by/bulk-confirm", response_model=GenericResponse)
async def bulk_confirm_initials_by_api(
        payload: BulkConfirmInitialsByIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):

    result = await _bulk_confirm(payload.letter_ids, payload.notes, db, current_user)
    return GenericResponse(message=f"Confirmed {len(result['confirmed'])} letter(s)", data=result)

@router.patch("/{letter_id}/{attribute}",
              summary="Switch letter attribute (status, assignee, department)",
              response_model=GenericResponse)
async def switch_attribute(
        letter_id: int,
        attribute: SwitchAttributeType,
        payload: SwitchLetterAttribute,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    logger.debug(f"Request to switch attribute: {attribute.value}")

    if attribute == SwitchAttributeType.status:
        has_permission("letter.change_status")
    elif attribute == SwitchAttributeType.assignee:
        has_permission("letter.assign")
    elif attribute == SwitchAttributeType.department:
        has_permission("letter.change_department")
    else:
        raise ValueError("Invalid attribute type")

    response = await switch_letter_attribute(
        letter_id,
        attribute.value,
        payload.current_id,
        payload.next_id,
        current_user,
        db,
    )
    return GenericResponse(data=response, message="Letter attribute switched successfully")

@router.post("/download-excel/")
async def download_letters_excel(
        excel_filter: LetterExcelFilter,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    logger.debug(f"Request to download letters in excel format with filters: {excel_filter}")

    if "letter.xdownload" not in current_user.permissions:
        raise UnauthorizedException('User does not have the required permission')

    excel_bytes = await letters_excel(excel_filter, current_user, db)
    return StreamingResponse(
        excel_bytes,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=letters.xlsx'}
    )


@router.get("/code/{date_time}", response_model=GenericResponse)
async def generate_code(
        db: DbSession,
        date_time: datetime = Path(description="DateTime to generate code for")
):
    logger.debug(f"Request to get letter code for datetime: {date_time}")

    code = await generate_letter_code(date_time, db)
    return GenericResponse(data=code, message="Letter code generated successfully")


@router.get("/stats/", response_model=GenericResponse)
async def get_letter_stats_api(
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    logger.debug("Request to get letter stats")

    stats = await get_letter_stats(current_user, db)
    return GenericResponse(data=stats, message="Letter stats fetched successfully")


@router.get("/{letter_id}/duplicate", response_model=GenericResponse)
async def duplicate_letter_api(
        db: DbSession,
        letter_id: int = Path(...),
        _=Depends(has_permission("letter.duplicate"))
):
    logger.debug(f"Request to duplicate letter with ID: {letter_id}")

    new_letter_data = await duplicate_letter(letter_id, db)
    return GenericResponse(data=new_letter_data, message="Letter duplicated successfully")


class LetterAssignmentIn(BaseModel):
    status_id: Optional[int] = None
    department_ids: List[int] = []
    assignee_ids: List[int] = []
    file_name: Optional[str] = None   # NEW
    recommended_to_id: Optional[int] = None  # NEW — separate from assignee_ids, see service/letter.py
    forwarded_to_id: Optional[int] = None  # NEW — separate from assignee_ids and recommended_to_id; no status required
    initials_by_user_id: Optional[int] = None  # NEW — who initialled the reply
    initials_by_notes: Optional[str] = None     # NEW
    order_by_role_id: Optional[int] = None
    order_by_action_id: Optional[int] = None

@router.put("/assignment/{letter_id}", response_model=GenericResponse)
async def update_letter_assignment_api(
        letter_id: int,
        payload: LetterAssignmentIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    allowed = {
        'letter.change_status', 'letter.change_department', 'letter.assign', 'letter.forward',
        'letter.initials_by', 'letter.order_by',   # NEW
    } & set(current_user.permissions)
    if not allowed:
        raise UnauthorizedException('User does not have the required permission')

    await _update_assignment(
        letter_id, payload.status_id, payload.department_ids, payload.assignee_ids, db,
        username=f"{current_user.first_name} {current_user.last_name}",
        email=current_user.email,
        allowed_status_ids=current_user.allowed_status_ids,
        can_change_status='letter.change_status' in current_user.permissions,
        can_change_department='letter.change_department' in current_user.permissions,
        can_assign='letter.assign' in current_user.permissions,
        current_user_id=current_user.id,  # NEW
        file_name=payload.file_name,
        allowed_department_ids=current_user.allowed_department_ids,  # NEW
        allowed_assignee_role_ids=current_user.allowed_assignee_role_ids,  # NEW
        recommended_to_id=payload.recommended_to_id,  # NEW
        can_forward='letter.forward' in current_user.permissions,  # NEW
        forwarded_to_id=payload.forwarded_to_id,  # NEW
        can_initials_by='letter.initials_by' in current_user.permissions,   # NEW
        initials_by_user_id=payload.initials_by_user_id,                     # NEW
        initials_by_notes=payload.initials_by_notes,                          # NEW
        can_order_by='letter.order_by' in current_user.permissions,          # NEW
        order_by_role_id=payload.order_by_role_id,
        order_by_action_id = payload.order_by_action_id,
        order_by_set_by_user_id = current_user.id,                            # NEW — always the actual logged-in user, never client-supplied
    )
    return GenericResponse(message="Letter updated successfully")

@router.get("/{letter_id}/history", response_model=GenericResponse)
async def get_letter_history_api(
        db: DbSession,
        letter_id: int = Path(...),
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
):
    history = db.query(HistoryModel).filter(
        HistoryModel.letter_id == letter_id
    ).order_by(HistoryModel.create_datetime.desc()).all()

    result = [HistoryModelOut.model_validate(h) for h in history]
    return GenericResponse(data=result, message="History fetched successfully")




@router.put("/{letter_id}/cheque", response_model=GenericResponse)
async def update_cheque_deposit_api(
        letter_id: int,
        payload: ChequeDepositIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("letter.cheque_update")),
):
    await _update_cheque_deposit(letter_id, payload, db, current_user)
    return GenericResponse(message="Cheque deposit status updated successfully")



@router.put("/{letter_id}/assignee-status", response_model=GenericResponse)
async def update_assignee_status_api(
        letter_id: int,
        payload: LetterAssigneeStatusIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    logger.debug(f"Request to update assignee status for letter {letter_id}")
    await _update_assignee_status(letter_id, current_user.id, payload, db, current_user)
    return GenericResponse(message="Your status has been updated successfully")



# ADD THESE THREE ENDPOINTS TO api/letter.py.
# IMPORTANT: place them ABOVE the existing
#   @router.patch("/{letter_id}/{attribute}", ...)
# route in the file (or anywhere before it) — both that route and
# "/deleted/list" are two-segment paths, and keeping the specific static
# path earlier avoids any ambiguity in how the router resolves them.
#
# Also make sure this import line is present near the top of api/letter.py:
#   get_deleted_letters_service, restore_letter_service, permanently_delete_letter_service,
# added to the "from service.letter import (...)" block.

@router.get("/deleted/list", response_model=GenericResponsePaginated)
async def get_deleted_letters_api(
        db: DbSession,
        page: int = 1,
        page_size: int = 10,
        _=Depends(has_permission("letter.view_deleted")),
):
    logger.debug("Request to list deleted letters")
    total, result = await get_deleted_letters_service(page, page_size, db)
    total_pages = ceil(total / page_size) if page_size else 1
    return GenericResponsePaginated(
        data=result, message="Deleted letters fetched successfully",
        total=total, total_pages=total_pages, page=page, page_size=page_size,
    )


@router.put("/{letter_id}/restore", response_model=GenericResponse)
async def restore_letter_api(
        db: DbSession,
        letter_id: int = Path(...),
        _=Depends(has_permission("letter.view_deleted")),
):
    logger.debug(f"Request to restore letter {letter_id}")
    await restore_letter_service(letter_id, db)
    return GenericResponse(message="Letter restored successfully")


@router.delete("/{letter_id}/permanent", response_model=GenericResponse)
async def permanently_delete_letter_api(
        db: DbSession,
        letter_id: int = Path(...),
        _=Depends(has_permission("letter.permanent_delete")),
):
    logger.debug(f"Request to permanently delete letter {letter_id}")
    await permanently_delete_letter_service(letter_id, db)
    return GenericResponse(message="Letter permanently deleted")


class InitialsByAssignIn(BaseModel):
    initials_by_pending_user_id: Optional[int] = None


class InitialsByConfirmIn(BaseModel):
    notes: Optional[str] = None



@router.put("/{letter_id}/initials-by/confirm", response_model=GenericResponse)
async def confirm_initials_by_api(
        letter_id: int,
        payload: InitialsByConfirmIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):

    await _confirm_initials_by(letter_id, payload.notes, db, current_user)
    return GenericResponse(message="Initials confirmed")


@router.put("/{letter_id}/initials-by/assign", response_model=GenericResponse)
async def assign_initials_by_api(
        letter_id: int,
        payload: InitialsByAssignIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("letter.initials_by_manage")),
):

    await _assign_initials_by(letter_id, payload.initials_by_pending_user_id, db, current_user)
    return GenericResponse(message="Initials By request sent")
