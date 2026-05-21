# import logging
# from datetime import datetime
# from pathlib import Path
#
# import uvicorn
# from fastapi import FastAPI, Request, Depends, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pytz import utc
# from starlette.responses import FileResponse
#
# from api import all_routers
# from config.config import ATTACHMENTS_DIR, SERVER_PORT, ALLOW_ORIGINS
# from config.logger import setup_logger
# from crud.refresh_token import clean_expired_tokens
# from db.models import models
# from db.session import engine, get_db
# from exception.exception_handler import add_exception_handler
# from utils.auth import get_current_user
#
# setup_logger()
# logger = logging.getLogger(__name__)
# app = FastAPI(
#     description='COOP Postal Management System Core Service',
#     version="1.0",
#     title='COOP PMS Core Service'
# )
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_origins=ALLOW_ORIGINS
# )
#
#
# @app.middleware("http")
# async def clean_expired_tokens_middleware(request: Request, call_next):
#     # Clean expired tokens every hour (based on request timestamp)
#     current_hour = datetime.now(utc).hour
#     if current_hour % 1 == 0 and datetime.now(utc).minute < 5:
#         db = next(get_db())
#         await clean_expired_tokens(db)
#         logger.info("Expired refresh tokens cleaned")
#
#     response = await call_next(request)
#     return response
#
#
# @app.get("/attachments/{file_path:path}")
# def serve_attachment(
#         file_path: str,
#         _=Depends(get_current_user)
# ):
#     attachments_dir_path = Path(ATTACHMENTS_DIR)
#     requested_path = attachments_dir_path / file_path
#     try:
#         requested_path = requested_path.resolve(strict=True)
#         if not str(requested_path).startswith(str(attachments_dir_path.resolve())):
#             raise HTTPException(status_code=403, detail="Access forbidden")
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="File not found")
#
#     return FileResponse(requested_path)
#
#
# app.include_router(all_routers)
# add_exception_handler(app)
# models.Base.metadata.create_all(engine)
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)



import logging
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pytz import utc
from starlette.responses import FileResponse

from api import all_routers
from config.config import ATTACHMENTS_DIR, SERVER_PORT, ALLOW_ORIGINS
from config.logger import setup_logger
from crud.refresh_token import clean_expired_tokens
from db.models import models
from db.session import engine, get_db
from exception.exception_handler import add_exception_handler
from utils.auth import get_current_user

setup_logger()
logger = logging.getLogger(__name__)
app = FastAPI(
    description='COOP Postal Management System Core Service',
    version="1.0",
    title='COOP PMS Core Service'
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    allow_origins=ALLOW_ORIGINS,  # Must NOT contain "*" — see config fix below
    expose_headers=["Set-Cookie"],  # 👈 Required so browser can read Set-Cookie
)


@app.middleware("http")
async def clean_expired_tokens_middleware(request: Request, call_next):
    current_hour = datetime.now(utc).hour
    if current_hour % 1 == 0 and datetime.now(utc).minute < 5:
        db = next(get_db())
        await clean_expired_tokens(db)
        logger.info("Expired refresh tokens cleaned")

    response = await call_next(request)
    return response


@app.get("/attachments/{file_path:path}")
def serve_attachment(
        file_path: str,
        _=Depends(get_current_user)
):
    attachments_dir_path = Path(ATTACHMENTS_DIR)
    requested_path = attachments_dir_path / file_path
    try:
        requested_path = requested_path.resolve(strict=True)
        if not str(requested_path).startswith(str(attachments_dir_path.resolve())):
            raise HTTPException(status_code=403, detail="Access forbidden")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(requested_path)


app.include_router(all_routers)
add_exception_handler(app)
models.Base.metadata.create_all(engine)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)