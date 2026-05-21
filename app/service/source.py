from logging import getLogger

from sqlalchemy.orm import Session

from crud.source import (
    save_source,
    fetch_active_sources,
    update_source,
    get_source_by_id
)
from db.models.models import Source
from exception.exception import NoDataFoundException
from models.source import SourceModelIn, SourceModelOut

logger = getLogger(__name__)


async def create_source(source_model: SourceModelIn, db: Session):
    logger.info("Create source process started")

    source = Source(
        name=source_model.name
    )

    source_db = await save_source(source, db)
    source_response = SourceModelOut.model_validate(source_db)

    logger.info("Create source process end")
    return source_response


async def get_active_sources(db: Session):
    logger.info("Fetching active sources started")
    sources = await fetch_active_sources(db)

    sources_list = [
        SourceModelOut.model_validate(sources) for sources in sources
    ]

    logger.info("Fetching active sources end")
    return sources_list


async def update_source_by_id(source_id: int, source_model: SourceModelIn, db: Session):
    logger.info(f"Update source {source_id} process started")

    source_db = await get_source_by_id(source_id, db)
    if not source_db:
        raise NoDataFoundException(f"Source with ID {source_id} not found for update")

    update_data = source_model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source_db, field, value)

    updated_source = await update_source(source_db, db)
    source_response = SourceModelOut.model_validate(updated_source)

    logger.info(f"Update source {source_id} process end")
    return source_response


async def deactivate_source_by_id(source_id: int, db: Session):
    logger.info(f"Deactivate source {source_id} process started")

    source_db = await get_source_by_id(source_id, db)
    if not source_db:
        raise NoDataFoundException(f"Source with ID {source_id} not found for deactivate")

    source_db.is_active = False
    updated_source = await update_source(source_db, db)
    source_response = SourceModelOut.model_validate(updated_source)

    logger.info(f"Deactivate source {source_id} process end")
    return source_response
