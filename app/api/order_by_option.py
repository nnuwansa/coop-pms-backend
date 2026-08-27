import logging
from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.order_by_option import OrderByOptionIn, OrderByOptionUpdate
from service.order_by_option import (
    create_order_by_option, quick_add_order_by_option, get_order_by_options,
    update_order_by_option, delete_order_by_option
)
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/order-by-option", tags=["Order By Option"])


# used by BOTH the admin System Settings page and the Letter View picker
# @router.get("/list", response_model=GenericResponse)
# async def list_order_by_options(db: DbSession,category: str = None, _=Depends(get_current_user)):
#     options = await get_order_by_options(db, active_only=not include_inactive, category=category)
#     return GenericResponse(success=True, message="Order By options fetched successfully", data=options)
@router.get("/list", response_model=GenericResponse)
async def list_order_by_options(
        db: DbSession,
        category: str = None,
        include_inactive: bool = False,
        _=Depends(get_current_user)
):
    options = await get_order_by_options(db, active_only=not include_inactive, category=category)
    return GenericResponse(success=True, message="Order By options fetched successfully", data=options)

@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_order_by_option_endpoint(
        payload: OrderByOptionIn, db: DbSession,
        current_user=Depends(has_permission("order_by_option.manage"))
):
    result = await create_order_by_option(payload, db, performed_by=getattr(current_user, "email", None))
    return GenericResponse(success=True, message="Order By option added successfully", data=result)

@router.put("/{option_id}", response_model=GenericResponse)
async def update_order_by_option_endpoint(
        option_id: int, payload: OrderByOptionUpdate, db: DbSession,
        current_user=Depends(has_permission("order_by_option.manage"))
):
    result = await update_order_by_option(option_id, payload, db)
    return GenericResponse(success=True, message="Order By option updated successfully", data=result)


@router.delete("/{option_id}", response_model=GenericResponse)
async def delete_order_by_option_endpoint(
        option_id: int, db: DbSession,
        current_user=Depends(has_permission("order_by_option.manage"))
):
    await delete_order_by_option(option_id, db)
    return GenericResponse(success=True, message="Order By option removed successfully")


# inline quick-add from the Letter View — gated by letter.order_by, NOT
# order_by_option.manage, so anyone who can pick Order By on a letter can
# also add a missing title without needing the full admin permission
@router.post("/quick-add", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def quick_add_order_by_option_endpoint(
        payload: OrderByOptionIn, db: DbSession,
        current_user=Depends(has_permission("letter.order_by"))
):
    result = await quick_add_order_by_option(payload.name, payload.category, db, performed_by=getattr(current_user, "email", None))
    return GenericResponse(success=True, message="Title added successfully", data=result)