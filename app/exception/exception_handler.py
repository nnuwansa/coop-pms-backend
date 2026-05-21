from logging import getLogger

from fastapi import FastAPI, Request
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from exception.exception import NoDataFoundException, CodeExistException, UnsupportedFileTypeException, \
    DuplicateEntryException, UnauthorizedException, UnRefreshingException

logger = getLogger(__name__)


def add_exception_handler(app: FastAPI):
    @app.exception_handler(Exception)
    async def handle_generic_exception(_: Request, exc: Exception):
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': str(exc)})

    @app.exception_handler(NoDataFoundException)
    async def handle_no_data_found_exception(_: Request, exc: NoDataFoundException):
        logger.error(exc)
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': exc.message})

    @app.exception_handler(CodeExistException)
    async def handle_code_exist_exception(_: Request, exc: CodeExistException):
        logger.error(exc)
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': exc.message})

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, exc: IntegrityError):
        logger.exception(exc)
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': 'Unfortunately database operation is failed'})

    @app.exception_handler(UnsupportedFileTypeException)
    async def handle_integrity_error(_: Request, exc: UnsupportedFileTypeException):
        logger.error(exc)
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': 'This file type is not supported'})

    @app.exception_handler(DuplicateEntryException)
    async def handle_duplicate_entry(_: Request, exc: DuplicateEntryException):
        logger.warning(exc)
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST,
                            content={'success': False,
                                     'message': exc.message})

    @app.exception_handler(UnauthorizedException)
    async def handle_unauthorized(_: Request, exc: UnauthorizedException):
        logger.error(exc)
        response = JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            content={'success': False, 'message': exc.message}
        )
        return response

    @app.exception_handler(UnRefreshingException)
    async def handle_un_refreshing(_: Request, exc: UnRefreshingException):
        logger.error(exc)
        response = JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            content={'success': False, 'message': exc.message}
        )
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="is_authenticated", path="/")
        response.delete_cookie(key="refresh_token", path="/v1/auth/refresh")
        return response
