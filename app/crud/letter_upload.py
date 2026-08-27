from logging import getLogger

from sqlalchemy.orm import Session

from db.models.models import LetterUpload

logger = getLogger(__name__)


async def save_upload(upload: LetterUpload, db: Session) -> LetterUpload:
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


async def get_uploads_by_user(user_id: int, db: Session):
    return (
        db.query(LetterUpload)
        .filter(LetterUpload.uploaded_by_id == user_id, LetterUpload.is_active)
        .order_by(LetterUpload.create_datetime.desc())
        .all()
    )


async def get_all_uploads(db: Session):
    return (
        db.query(LetterUpload)
        .filter(LetterUpload.is_active)
        .order_by(LetterUpload.create_datetime.desc())
        .all()
    )


async def get_upload_by_id(upload_id: int, db: Session):
    return db.query(LetterUpload).filter(
        LetterUpload.id == upload_id, LetterUpload.is_active
    ).first()


async def soft_delete_upload(upload: LetterUpload, db: Session) -> LetterUpload:
    upload.is_active = False
    db.commit()
    db.refresh(upload)
    return upload