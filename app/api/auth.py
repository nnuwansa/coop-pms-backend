import logging

from fastapi import APIRouter, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm

from db.session import DbSession
from models.response import GenericResponse
from models.system_user import SystemUserModelOut, SystemUserWithPermissionsModelOut
from service.auth import login_user, logout_user, generate_access_token
from utils.auth import get_current_user, validate_refresh_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/auth",
    tags=["Authentication"]
)


@router.post("/login", response_model=GenericResponse)
async def login(
        response: Response,
        db: DbSession,
        form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.debug(f'Login request for user: {form_data.username}')
    await login_user(
        email=form_data.username,
        password=form_data.password,
        response=response,
        db=db
    )

    return GenericResponse(
        success=True,
        message="Login successful"
    )


@router.post("/logout", response_model=GenericResponse)
async def logout(
        response: Response,
        db: DbSession,
        current_user: SystemUserModelOut = Depends(get_current_user)
):
    logger.debug(f'Logout request for user: {current_user.email}')
    await logout_user(current_user.id, response, db)
    return GenericResponse(
        success=True,
        message="Logout successful"
    )


@router.post("/refresh", response_model=GenericResponse)
async def refresh_token(
        response: Response,
        db: DbSession,
        user_id: int = Depends(validate_refresh_token)
):
    logger.debug(f'Refresh token request for user ID: {user_id}')
    await generate_access_token(user_id, response, db)
    return GenericResponse(
        success=True,
        message="Token refreshed successfully"
    )


@router.get("/me", response_model=GenericResponse)
def get_current_user_info(current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)):
    logger.debug(f'Get current user info request for user: {current_user.email}')
    return GenericResponse(
        success=True,
        message="User info retrieved successfully",
        data=current_user
    )
