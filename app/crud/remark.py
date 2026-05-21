from sqlalchemy.orm import Session

from db.models.models import Remark


async def create_remark(remark: Remark, db: Session) -> Remark:
    db.add(remark)
    db.flush()
    return remark


async def get_active_remark(remark_id: int, db: Session) -> Remark | None:
    return db.query(Remark).filter(Remark.id == remark_id and Remark.is_active).first()


async def update_remark_db(remark: Remark, db: Session) -> Remark:
    db.commit()
    db.refresh(remark)
    return remark
