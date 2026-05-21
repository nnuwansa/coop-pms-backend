import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.source import SourceModelIn
from service.source import (
    create_source,
    get_active_sources,
    update_source_by_id,
    deactivate_source_by_id,
)
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/source",
    tags=["Source"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create(source: SourceModelIn, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f"Request to create source: {source}")
    created_source = await create_source(source, db)
    return GenericResponse(success=True, message="Source created successfully", data=created_source)


@router.get("/list", response_model=GenericResponse)
async def list_sources(db: DbSession):
    logger.debug("Request to list active sources")
    sources = await get_active_sources(db)
    return GenericResponse(success=True, message="Active sources fetched successfully", data=sources)


@router.put("/{source_id}", response_model=GenericResponse)
async def update_source(source_id: int, source_model: SourceModelIn, db: DbSession,
                        _=Depends(has_permission("settings.view"))):
    logger.debug(f"Request to update source ID {source_id} with data: {source_model}")
    updated_source = await update_source_by_id(source_id, source_model, db)

    return GenericResponse(success=True, message="Source updated successfully", data=updated_source)


@router.delete("/{source_id}", response_model=GenericResponse)
async def delete_source(source_id: int, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f"Request to deactivate source ID {source_id}")
    deleted_source = await deactivate_source_by_id(source_id, db)

    return GenericResponse(
        success=True, message="Source deactivated successfully", data=deleted_source
    )
