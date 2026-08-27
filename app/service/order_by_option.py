from logging import getLogger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models.models import OrderByOption
from exception.exception import DuplicateEntryException
from models.order_by_option import OrderByOptionIn, OrderByOptionUpdate

logger = getLogger(__name__)

from models.order_by_option import OrderByOptionIn, OrderByOptionUpdate, OrderByOptionOut


async def create_order_by_option(payload: OrderByOptionIn, db: Session, performed_by: str = None):
    existing = db.query(OrderByOption).filter(OrderByOption.name == payload.name.strip()).first()
    if existing:
        raise DuplicateEntryException("This title already exists")

    option = OrderByOption(name=payload.name.strip(), category=payload.category, is_active=True, created_by=performed_by)
    db.add(option)
    db.commit()
    db.refresh(option)
    return OrderByOptionOut.model_validate(option)   # FIXED — was returning raw SQLAlchemy object


async def quick_add_order_by_option(name: str, category: str, db: Session, performed_by: str = None):
    return await create_order_by_option(OrderByOptionIn(name=name, category=category), db, performed_by)

async def get_order_by_options(db: Session, active_only: bool = True, category: str = None):
    q = db.query(OrderByOption)
    if active_only:
        q = q.filter(OrderByOption.is_active == True)
        if category:
           q = q.filter(OrderByOption.category == category)
    options = q.order_by(OrderByOption.name).all()
    return [OrderByOptionOut.model_validate(o) for o in options]   # FIXED — same issue, list version


async def update_order_by_option(option_id: int, payload: OrderByOptionUpdate, db: Session):
    option = db.query(OrderByOption).filter(OrderByOption.id == option_id).first()
    if not option:
        return None
    if payload.name is not None:
        option.name = payload.name.strip()
        if payload.category is not None:
           option.category = payload.category
    if payload.is_active is not None:
        option.is_active = payload.is_active
    try:
        db.commit()
        db.refresh(option)
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e.orig):
            raise DuplicateEntryException("This title already exists")
        raise e
    return OrderByOptionOut.model_validate(option)   # FIXED


async def delete_order_by_option(option_id: int, db: Session):
    option = db.query(OrderByOption).filter(OrderByOption.id == option_id).first()
    if not option:
        return None
    option.is_active = False
    db.commit()
    return OrderByOptionOut.model_validate(option)   # FIXED