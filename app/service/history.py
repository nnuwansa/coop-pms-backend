from logging import getLogger

from sqlalchemy.orm import Session

from crud.history import save_history
from db.models.models import History

logger = getLogger(__name__)


async def generate_history(_from, _to, attribute: str, username: str, email: str, letter_id: int, db: Session):
    logger.info("History generating process started")

    if attribute == 'assignee':
        _to = f"{_to.first_name} {_to.last_name}"
        _from = f"{_from.first_name} {_from.last_name}" if _from else None
    else:
        _to = _to.name
        _from = _from.name if _from else None

    capitalized_attribute = attribute[0].upper() + attribute[1:].lower()

    if _from is None:
        description = f"{capitalized_attribute} set to {_to}"
    else:
        description = f"{capitalized_attribute} changed from {_from} to {_to}"

    history = History(
        description=description,
        username=username,
        email=email,
        letter_id=letter_id
    )

    await save_history(history, db)
    logger.info("History generating process ended")
