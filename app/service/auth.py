# import logging
# from datetime import timedelta
#
# from fastapi import Response
# from sqlalchemy.orm import Session
#
# from config.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, FE_DOMAIN, HTTPS_ENABLED
# from crud.refresh_token import save_refresh_token, revoke_refresh_token
# from crud.system_user import get_user_by_email, get_active_user_by_id
# from db.models.models import RefreshToken
# from exception.exception import UnauthorizedException
# from utils.security import verify_password, create_access_token, create_refresh_token
#
# logger = logging.getLogger(__name__)
#
#
# async def login_user(email: str, password: str, response: Response, db: Session):
#     logger.info("Logging service process started")
#     user = await get_user_by_email(email, db)
#
#     if not user:
#         raise UnauthorizedException("Incorrect username or password")
#
#     if not user.is_active:
#         raise UnauthorizedException("User is not activated, please contact system administrator")
#
#     if not await verify_password(password, user.password):
#         raise UnauthorizedException("Incorrect username or password")
#     # Both return same message for security reasons
#
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = await create_access_token(
#         subject=user.id,
#         expires_delta=access_token_expires,
#         permissions=[permission.code for permission in user.role.permissions]
#     )
#
#     refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
#     refresh_token, expires_at = await create_refresh_token(
#         subject=user.id,
#         expires_delta=refresh_token_expires)
#
#     refresh_token_db = RefreshToken(
#         user_id=user.id,
#         token=refresh_token,
#         expires_at=expires_at
#     )
#     await save_refresh_token(refresh_token_db, db)
#
#     # Set tokens as HTTP-only cookies
#     response.set_cookie(
#         key="access_token",
#         value=access_token,
#         httponly=True,
#         max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#         expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#         path="/",  # Available to all API routes
#         samesite="none",
#         # domain=FE_DOMAIN,  # Set to your frontend domain
#         secure=True,  # Set to False in development if not using HTTPS
#     )
#
#     response.set_cookie(
#         key="refresh_token",
#         value=refresh_token,
#         httponly=True,
#         max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
#         expires=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
#         path="/v1/auth/refresh",  # Only sent to the refresh endpoint
#         samesite="none",
#         secure=True,  # Set to False in development if not using HTTPS
#     )
#
#     response.set_cookie(
#         key="is_authenticated",
#         value='true',
#         httponly=True,
#         max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
#         expires=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
#         path="/",
#         samesite="none",
#         # domain=FE_DOMAIN,  # Set to your frontend domain
#         secure=True,
#     )
#
#     logger.info("Logging service process ended")
#
#
# async def logout_user(user_id: int, response: Response, db: Session):
#     """Logout user by revoking their refresh token and clearing cookies."""
#
#     logger.info("Logout service process started")
#     await revoke_refresh_token(db, user_id)
#
#     response.delete_cookie(key="access_token", path="/")
#     response.delete_cookie(key="is_authenticated", path="/")
#     response.delete_cookie(key="refresh_token", path="/v1/auth/refresh")
#
#     logger.info("Logout service process ended")
#
#
# async def generate_access_token(user_id: int, response: Response, db: Session):
#     """Generate new access using valid refresh token."""
#     logger.info("Generate access token service process started")
#     user = await get_active_user_by_id(user_id, db)
#
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = await create_access_token(
#         subject=user_id,
#         expires_delta=access_token_expires,
#         permissions=[permission.code for permission in user.role.permissions]
#     )
#
#     # Set new tokens as HTTP-only cookies
#     response.set_cookie(
#         key="access_token",
#         value=access_token,
#         httponly=True,
#         max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#         expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#         path="/",  # Available to all API routes
#         samesite="none",
#         # domain=FE_DOMAIN,  # Set to your frontend domain
#         secure=True,  # Set to False in development if not using HTTPS
#     )
#     logger.info("Generate access token service process ended")



import logging
from datetime import timedelta

from fastapi import Response
from sqlalchemy.orm import Session

from config.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, FE_DOMAIN, HTTPS_ENABLED
from crud.refresh_token import save_refresh_token, revoke_refresh_token
from crud.system_user import get_user_by_email, get_active_user_by_id
from db.models.models import RefreshToken
from exception.exception import UnauthorizedException
from utils.security import verify_password, create_access_token, create_refresh_token

logger = logging.getLogger(__name__)


async def login_user(email: str, password: str, response: Response, db: Session):
    logger.info("Logging service process started")
    user = await get_user_by_email(email, db)

    if not user:
        raise UnauthorizedException("Incorrect username or password")

    if not user.is_active:
        raise UnauthorizedException("User is not activated, please contact system administrator")

    if not await verify_password(password, user.password):
        raise UnauthorizedException("Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
        permissions=[permission.code for permission in user.role.permissions]
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token, expires_at = await create_refresh_token(
        subject=user.id,
        expires_delta=refresh_token_expires
    )

    refresh_token_db = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    await save_refresh_token(refresh_token_db, db)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="none" if HTTPS_ENABLED else "lax",  # 👈 "none" requires secure=True
        secure=HTTPS_ENABLED,                          # 👈 use env variable
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        expires=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/v1/auth/refresh",
        samesite="none" if HTTPS_ENABLED else "lax",  # 👈
        secure=HTTPS_ENABLED,                          # 👈
    )

    response.set_cookie(
        key="is_authenticated",
        value="true",
        httponly=False,   # 👈 must be False so frontend JS can read this one
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        expires=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
        samesite="none" if HTTPS_ENABLED else "lax",  # 👈
        secure=HTTPS_ENABLED,                          # 👈
    )

    logger.info("Logging service process ended")


async def logout_user(user_id: int, response: Response, db: Session):
    logger.info("Logout service process started")
    await revoke_refresh_token(db, user_id)

    response.delete_cookie(key="access_token", path="/", samesite="none" if HTTPS_ENABLED else "lax", secure=HTTPS_ENABLED)
    response.delete_cookie(key="is_authenticated", path="/", samesite="none" if HTTPS_ENABLED else "lax", secure=HTTPS_ENABLED)
    response.delete_cookie(key="refresh_token", path="/v1/auth/refresh", samesite="none" if HTTPS_ENABLED else "lax", secure=HTTPS_ENABLED)

    logger.info("Logout service process ended")


async def generate_access_token(user_id: int, response: Response, db: Session):
    logger.info("Generate access token service process started")
    user = await get_active_user_by_id(user_id, db)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        subject=user_id,
        expires_delta=access_token_expires,
        permissions=[permission.code for permission in user.role.permissions]
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="none" if HTTPS_ENABLED else "lax",  # 👈
        secure=HTTPS_ENABLED,                          # 👈
    )
    logger.info("Generate access token service process ended")