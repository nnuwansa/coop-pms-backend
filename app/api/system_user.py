# import logging
# from math import ceil
# from typing import Optional
#
# from fastapi import APIRouter, Depends
# from starlette.status import HTTP_201_CREATED
#
# from db.session import DbSession
# from models.response import GenericResponse, GenericResponsePaginated
# from models.system_user import SystemUserModelIn, SystemUserModelUpdate, SystemUserFilter
# from service.system_user import create_system_user, \
#     get_all_system_user_full_names_service, update_system_user_info, delete_system_user_info, get_list_users, \
#     get_system_user_stats
# from utils.auth import get_current_user, has_permission
#
# logger = logging.getLogger(__name__)
#
# router = APIRouter(
#     prefix="/v1/system_user",
#     tags=["System User"]
# )
#
#
# @router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
# async def create_system_user_endpoint(
#         user: SystemUserModelIn,
#         db: DbSession
# ):
#     logger.debug(f'Request to create system user: {user}')
#     user_response = await create_system_user(user, db)
#
#     return GenericResponse(success=True, message="User account created successfully", data=user_response)
#
#
# @router.get("/names", response_model=GenericResponse)
# async def get_all_system_user_full_names_endpoint(
#         db: DbSession,
#         _=Depends(get_current_user)
# ):
#     logger.debug('Request to fetch full names for all system users')
#     full_names = await get_all_system_user_full_names_service(db)
#
#     return GenericResponse(success=True, message="System user fetched successfully", data=full_names)
#
#
# @router.put("/{user_id}", response_model=GenericResponse)
# async def update_system_user_endpoint(
#         user_id: int,
#         user_model: SystemUserModelUpdate,
#         db: DbSession,
#         _=Depends(has_permission("user.view"))
# ):
#     logger.debug(f'Request to update system user {user_id} with data: {user_model}')
#     updated_user = await update_system_user_info(user_id, user_model, db)
#
#     return GenericResponse(success=True, message="System user updated successfully", data=updated_user)
#
#
# @router.delete("/{user_id}", response_model=GenericResponse)
# async def delete_system_user_endpoint(
#         user_id: int,
#         db: DbSession,
#         _=Depends(has_permission("user.view"))
# ):
#     logger.debug(f'Request to delete system user {user_id}')
#     await delete_system_user_info(user_id, db)
#
#     return GenericResponse(success=True, message="System user deleted successfully")
#
#
# @router.post("/list", response_model=GenericResponsePaginated)
# async def get_users_api(
#         db: DbSession,
#         filters: Optional[SystemUserFilter] = None,
#         page: int = 1,
#         page_size: int = 10,
#         _=Depends(get_current_user)
# ):
#     logger.debug(f"Request to list users with filters: {filters}")
#
#     total, result = await get_list_users(filters, page, page_size, db)
#     total_pages = ceil(total / page_size) if page_size else 1
#
#     return GenericResponsePaginated(data=result, message="Users fetched successfully",
#                                     total=total,
#                                     total_pages=total_pages,
#                                     page=page, page_size=page_size)
#
#
# @router.get("/stats", response_model=GenericResponse)
# async def get_system_user_stats_endpoint(db: DbSession, _=Depends(get_current_user)):
#     logger.debug('Request to fetch system user stats')
#     stats = await get_system_user_stats(db)
#
#     return GenericResponse(success=True, message="System user stats fetched successfully", data=stats)



import logging
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse, GenericResponsePaginated
from models.system_user import SystemUserModelIn, SystemUserModelUpdate, SystemUserFilter
from service.system_user import create_system_user, \
    get_all_system_user_full_names_service, update_system_user_info, delete_system_user_info, get_list_users, \
    get_system_user_stats, get_user_history_service
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/system_user",
    tags=["System User"]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_system_user_endpoint(
        user: SystemUserModelIn,
        db: DbSession
):
    logger.debug(f'Request to create system user: {user}')
    # Public sign-up endpoint, so the user is registering themself
    user_response = await create_system_user(user, db, performed_by=user.email)

    return GenericResponse(success=True, message="User account created successfully", data=user_response)


@router.get("/names", response_model=GenericResponse)
async def get_all_system_user_full_names_endpoint(
        db: DbSession,
        _=Depends(get_current_user)
):
    logger.debug('Request to fetch full names for all system users')
    full_names = await get_all_system_user_full_names_service(db)

    return GenericResponse(success=True, message="System user fetched successfully", data=full_names)


@router.put("/{user_id}", response_model=GenericResponse)
async def update_system_user_endpoint(
        user_id: int,
        user_model: SystemUserModelUpdate,
        db: DbSession,
        current_user=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to update system user {user_id} with data: {user_model}')
    updated_user = await update_system_user_info(
        user_id, user_model, db,
        performed_by=getattr(current_user, "email", None)
    )

    return GenericResponse(success=True, message="System user updated successfully", data=updated_user)


@router.delete("/{user_id}", response_model=GenericResponse)
async def delete_system_user_endpoint(
        user_id: int,
        db: DbSession,
        current_user=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to delete system user {user_id}')
    await delete_system_user_info(user_id, db, performed_by=getattr(current_user, "email", None))

    return GenericResponse(success=True, message="System user deleted successfully")


@router.post("/list", response_model=GenericResponsePaginated)
async def get_users_api(
        db: DbSession,
        filters: Optional[SystemUserFilter] = None,
        page: int = 1,
        page_size: int = 10,
        _=Depends(get_current_user)
):
    logger.debug(f"Request to list users with filters: {filters}")

    total, result = await get_list_users(filters, page, page_size, db)
    total_pages = ceil(total / page_size) if page_size else 1

    return GenericResponsePaginated(data=result, message="Users fetched successfully",
                                     total=total,
                                     total_pages=total_pages,
                                     page=page, page_size=page_size)


@router.get("/stats", response_model=GenericResponse)
async def get_system_user_stats_endpoint(db: DbSession, _=Depends(get_current_user)):
    logger.debug('Request to fetch system user stats')
    stats = await get_system_user_stats(db)

    return GenericResponse(success=True, message="System user stats fetched successfully", data=stats)


@router.get("/{user_id}/history", response_model=GenericResponse)
async def get_system_user_history_endpoint(
        user_id: int,
        db: DbSession,
        _=Depends(get_current_user)
):
    logger.debug(f'Request to fetch history for system user {user_id}')
    history = await get_user_history_service(user_id, db)

    return GenericResponse(success=True, message="User history fetched successfully", data=history)