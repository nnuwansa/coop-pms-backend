from logging import getLogger

from sqlalchemy.orm import Session

from crud.organization import save_organization, get_all_active_organizations, get_organization_by_id, \
    update_organization_info
from db.models.models import Organization
from exception.exception import NoDataFoundException
from models.organization import OrganizationModelIn, OrganizationModelOut

logger = getLogger(__name__)


async def create_organization(organization_model: OrganizationModelIn, db: Session):
    logger.info("Create organization process started")

    organization = Organization(
        name=organization_model.name,
    )

    organization_db = await save_organization(organization, db)
    organization_response = OrganizationModelOut.model_validate(organization_db)

    logger.info("Create organization process ended")
    return organization_response


async def get_all_organizations(db: Session):
    logger.info("Get all organizations process started")

    organizations = await get_all_active_organizations(db)

    organizations_list = [
        OrganizationModelOut.model_validate(org) for org in organizations
    ]

    logger.info("Get all organizations process ended")
    return organizations_list


async def update_organization(organization_id: int, organization_model: OrganizationModelIn, db: Session):
    logger.info("Update organization process started for organization ID {organization_id}")

    organization_db = await get_organization_by_id(organization_id, db)
    if not organization_db:
        raise NoDataFoundException(f"Organization with ID {organization_id} not found for update")

    update_data = organization_model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization_db, field, value)

    updated_org = await update_organization_info(organization_db, db)
    organization_response = OrganizationModelOut.model_validate(updated_org)

    logger.info(f"Update organization process ended for organization ID {organization_id}")
    return organization_response


async def soft_delete_organization(organization_id: int, db: Session):
    logger.info(f"Soft delete organization process started for organization ID {organization_id}")

    organization_db = await get_organization_by_id(organization_id, db)
    if not organization_db:
        raise NoDataFoundException(f"Organization with ID {organization_id} not found for delete")

    organization_db.is_active = False
    updated_org = await update_organization_info(organization_db, db)
    organization_response = OrganizationModelOut.model_validate(updated_org)

    logger.info(f"Soft delete organization process ended for organization ID {organization_id}")
    return organization_response
