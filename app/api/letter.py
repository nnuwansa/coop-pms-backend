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
    update_letter_assignment as _update_assignment,
)
from service.remark import (
    create_remarks_and_attachments, update_remark_and_attachments,
    delete_remark_by_id, bind_remark_attachments, get_remark_history,
)
from utils.auth import get_current_user, has_permission
from models.letter import ChequeDepositIn
from service.letter import update_cheque_deposit as _update_cheque_deposit

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/letter",
    tags=["Letter"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=GenericResponse)
async def create_letter_api(
        letter: LetterModelIn,
        db: DbSession,
        _=Depends(has_permission("letter.create"))
):
    logger.debug(f"Request to create letter: {letter}")
    letter_obj = await create_letter(letter, db)
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

# @router.put("/assignment/{letter_id}", response_model=GenericResponse)
# async def update_letter_assignment_api(
#         letter_id: int,
#         payload: LetterAssignmentIn,
#         db: DbSession,
#         current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
#         _=Depends(has_permission("letter.update"))
# ):
#     await _update_assignment(
#         letter_id,
#         payload.status_id,
#         payload.department_ids,
#         payload.assignee_ids,
#         db,
#         username=f"{current_user.first_name} {current_user.last_name}",
#         email=current_user.email,
#         allowed_status_ids=current_user.allowed_status_ids,  # CHANGED — was role_id
#     )
#     return GenericResponse(message="Letter updated successfully")

@router.put("/assignment/{letter_id}", response_model=GenericResponse)
async def update_letter_assignment_api(
        letter_id: int,
        payload: LetterAssignmentIn,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    allowed = {'letter.change_status', 'letter.change_department', 'letter.assign'} & set(current_user.permissions)
    if not allowed:
        raise UnauthorizedException('User does not have the required permission')

    await _update_assignment(
        letter_id,
        payload.status_id,
        payload.department_ids,
        payload.assignee_ids,
        db,
        username=f"{current_user.first_name} {current_user.last_name}",
        email=current_user.email,
        allowed_status_ids=current_user.allowed_status_ids,
        can_change_status='letter.change_status' in current_user.permissions,
        can_change_department='letter.change_department' in current_user.permissions,
        can_assign='letter.assign' in current_user.permissions,
        file_name=payload.file_name,  # NEW
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
        _=Depends(has_permission("letter.update")),
):
    await _update_cheque_deposit(letter_id, payload, db, current_user)
    return GenericResponse(message="Cheque deposit status updated successfully")