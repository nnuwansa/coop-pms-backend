import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Depends
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.params import Cookie
from fastapi.security import OAuth2
from jose import JWTError, ExpiredSignatureError
from pytz import utc

from crud.refresh_token import get_refresh_token_by_token
from crud.system_user import get_active_user_by_id
from db.session import DbSession
from exception.exception import UnauthorizedException, UnRefreshingException
from models.system_user import SystemUserWithPermissionsModelOut
from utils.security import decode_token

logger = logging.getLogger(__name__)


class OAuth2CookieBearer(OAuth2):
    """Custom OAuth2 class that can extract tokens from cookies."""

    def __init__(
            self,
            token_url: str,
            scheme_name: Optional[str] = None,
            scopes: Optional[dict] = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": token_url, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        access_token = request.cookies.get("access_token")
        if access_token:
            return access_token

        if self.auto_error:
            raise UnauthorizedException("Not authenticated")
        return None


oauth2_scheme = OAuth2CookieBearer(token_url="/v1/auth/login")


async def get_current_user(
        db: DbSession,
        token: str = Depends(oauth2_scheme)
) -> SystemUserWithPermissionsModelOut:
    """Get current user from access token."""
    logger.info("Retrieving current user from access token started")
    try:
        payload = await decode_token(token, token_type="access")
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        allowed_status_ids = payload.get("allowed_status_ids", [])   # NEW

        if user_id is None or token_type != "access":
            raise UnauthorizedException("Invalid access token")

    except ExpiredSignatureError:
        raise UnauthorizedException("Token signature has expired")

    except JWTError as e:
        logger.exception(e)
        raise UnauthorizedException("Unable to decode access token")

    user = await get_active_user_by_id(int(user_id), db)
    if not user:
        raise UnauthorizedException("Valid user not exist")

    logger.info("Retrieving current user from access token ended")
    user_model = SystemUserWithPermissionsModelOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        department=user.department.name if user.department else None,
        department_id=user.department.id if user.department else None,
        role=user.role.name if user.role else None,
        permissions=[permission.code for permission in user.role.permissions],
        allowed_status_ids=allowed_status_ids,   # NEW
    )

    return user_model

async def validate_refresh_token(
        db: DbSession,
        refresh_token: Optional[str] = Cookie(None)
) -> int:
    """Validate refresh token from cookie."""
    logger.info("Validating refresh token started")
    if not refresh_token:
        raise UnRefreshingException("Refresh token missing")

    try:
        payload = await decode_token(refresh_token, token_type="refresh")
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "refresh":
            raise UnRefreshingException("Invalid refresh token")

        db_token = await get_refresh_token_by_token(refresh_token, db)
        if not db_token or db_token.is_revoked or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(utc):
            raise UnRefreshingException("Refresh token expired or revoked")

        logger.info("Validating refresh token ended")
        return int(user_id)

    except ExpiredSignatureError:
        raise UnRefreshingException("Refresh token signature has expired")

    except JWTError as e:
        logger.exception(e)
        raise UnRefreshingException("Invalid refresh token")


def has_permission(permission: str):
    async def permission_checker(
            current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user)
    ):
        if permission not in current_user.permissions:
            raise UnauthorizedException('User does not have the required permission')

    return permission_checker
