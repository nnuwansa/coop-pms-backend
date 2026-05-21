from logging import getLogger

from sqlalchemy.orm import Session

from db.models.models import Organization

logger = getLogger(__name__)


async def save_organization(organization: Organization, db: Session):
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


async def get_organization_by_id(org_id: int, db: Session):
    return db.query(Organization).filter(Organization.id == org_id).first()


async def get_all_active_organizations(db: Session):
    return db.query(Organization).filter(Organization.is_active).all()


async def delete_organization(org_id: Organization, db: Session):
    org_id.is_active = False
    db.commit()
    db.refresh(org_id)
    return org_id


async def update_organization_info(org_id: dict, db: Session):
    db.commit()
    db.refresh(org_id)
    return org_id
