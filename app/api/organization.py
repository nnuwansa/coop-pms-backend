import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.organization import OrganizationModelIn
from models.response import GenericResponse
from service.organization import create_organization, get_all_organizations, update_organization, \
    soft_delete_organization
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/organization",
    tags=["Organization"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_organization_endpoint(organization: OrganizationModelIn, db: DbSession,
                                       _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to create organization: {organization}')
    organization_response = await create_organization(organization, db)

    return GenericResponse(success=True, message="Organization created successfully", data=organization_response)


@router.get("/list", response_model=GenericResponse)
async def get_active_organizations_endpoint(db: DbSession):
    logger.debug('Request to fetch all active organizations')
    active_organizations = await get_all_organizations(db)

    return GenericResponse(success=True, message="Active organizations fetched successfully", data=active_organizations)


@router.put("/{organization_id}", response_model=GenericResponse)
async def update_organization_endpoint(organization_id: int, organization_model: OrganizationModelIn,
                                       db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to update organization {organization_id} with data: {organization_model}')
    updated_organization = await update_organization(organization_id, organization_model, db)

    return GenericResponse(success=True, message="Organization updated successfully", data=updated_organization)


@router.delete("/{organization_id}", response_model=GenericResponse)
async def delete_organization_endpoint(organization_id: int, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to soft delete organization {organization_id}')
    deleted_organization = await soft_delete_organization(organization_id, db)

    return GenericResponse(success=True, message="Organization deleted successfully", data=deleted_organization)
