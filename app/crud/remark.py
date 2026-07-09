# from sqlalchemy.orm import Session
#
# from db.models.models import Remark
#
#
# async def create_remark(remark: Remark, db: Session) -> Remark:
#     db.add(remark)
#     db.flush()
#     return remark
#
#
# # async def get_active_remark(remark_id: int, db: Session) -> Remark | None:
# #     return db.query(Remark).filter(Remark.id == remark_id and Remark.is_active).first()
# async def get_active_remark(remark_id: int, db: Session) -> Remark | None:
#     return db.query(Remark).filter(
#         Remark.id == remark_id,
#         Remark.is_active == True
#     ).first()
#
# async def update_remark_db(remark: Remark, db: Session) -> Remark:
#     db.commit()
#     db.refresh(remark)
#     return remark



from sqlalchemy.orm import Session

from db.models.models import Remark, RemarkHistory


async def create_remark(remark: Remark, db: Session) -> Remark:
    db.add(remark)
    db.flush()
    return remark


async def get_active_remark(remark_id: int, db: Session) -> Remark | None:
    return db.query(Remark).filter(
        Remark.id == remark_id,
        Remark.is_active == True
    ).first()


async def update_remark_db(remark: Remark, db: Session) -> Remark:
    db.commit()
    db.refresh(remark)
    return remark


async def create_remark_history(history: RemarkHistory, db: Session) -> RemarkHistory:
    db.add(history)
    db.flush()
    return history


async def get_remark_history_by_letter(letter_id: int, db: Session):
    return (
        db.query(RemarkHistory)
        .filter(RemarkHistory.letter_id == letter_id)
        .order_by(RemarkHistory.create_datetime.desc())
        .all()
    )