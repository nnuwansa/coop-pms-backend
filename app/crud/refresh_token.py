from datetime import datetime

from pytz import utc
from sqlalchemy.orm import Session

from db.models.models import RefreshToken


async def save_refresh_token(refresh_token: RefreshToken, db: Session):
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


async def revoke_refresh_token(db: Session, user_id: int):
    refresh_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    for token in refresh_tokens:
        token.is_revoked = True
    db.commit()


async def get_refresh_token_by_token(token: str, db: Session) -> RefreshToken:
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()


async def clean_expired_tokens(db: Session):
    db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(utc)
    ).delete()
    db.commit()
