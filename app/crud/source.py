from logging import getLogger

from db.models.models import Source

logger = getLogger(__name__)


async def save_source(source: Source, db):
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


async def fetch_active_sources(db):
    return db.query(Source).filter(Source.is_active).all()


async def get_source_by_id(source_id: int, db):
    return db.query(Source).filter(Source.id == source_id).first()


async def update_source(source: dict, db):
    db.commit()
    db.refresh(source)
    return source
