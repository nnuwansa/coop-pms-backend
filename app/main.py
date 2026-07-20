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
# # @app.middleware("http")
# # async def clean_expired_tokens_middleware(request: Request, call_next):
# #     # Clean expired tokens every hour (based on request timestamp)
# #     current_hour = datetime.now(utc).hour
# #     if current_hour % 1 == 0 and datetime.now(utc).minute < 5:
# #         db = next(get_db())
# #         await clean_expired_tokens(db)
# #         logger.info("Expired refresh tokens cleaned")
# #
# #     response = await call_next(request)
# #     return response
#
#
# @app.middleware("http")
# async def clean_expired_tokens_middleware(request: Request, call_next):
#     now = datetime.now(utc)
#     # Only run at the start of each hour (minute 0-4)
#     if now.minute < 5:
#         db = next(get_db())
#         try:
#             await clean_expired_tokens(db)
#             logger.info("Expired refresh tokens cleaned")
#         finally:
#             db.close()
#
#     response = await call_next(request)
#     return response
#
# @app.middleware("http")
# async def private_network_access_middleware(request: Request, call_next):
#     response = await call_next(request)
#     response.headers["Access-Control-Allow-Private-Network"] = "true"
#     return response
#
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
# # if __name__ == "__main__":
# #     uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_config=None)
#
#
#
#     scheduler = AsyncIOScheduler()
#
#
#     async def _run_reminder_job():
#         db = SessionLocal()
#         try:
#             await send_pending_letter_reminders(db)
#         finally:
#             db.close()
#
#
#     @app.on_event("startup")
#     async def start_scheduler():
#         scheduler.add_job(_run_reminder_job, "cron", hour=8, minute=0)  # daily at 08:00
#         scheduler.start()



import logging
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pytz import utc
from starlette.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api import all_routers
from config.config import ATTACHMENTS_DIR, SERVER_PORT, ALLOW_ORIGINS
from config.logger import setup_logger
from crud.refresh_token import clean_expired_tokens
from db.models import models
from db.session import engine, get_db, SessionLocal
from exception.exception_handler import add_exception_handler
from utils.auth import get_current_user
from service.reminders import send_pending_letter_reminders

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
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=ALLOW_ORIGINS
)


@app.middleware("http")
async def clean_expired_tokens_middleware(request: Request, call_next):
    now = datetime.now(utc)
    # Only run at the start of each hour (minute 0-4)
    if now.minute < 5:
        db = next(get_db())
        try:
            await clean_expired_tokens(db)
            logger.info("Expired refresh tokens cleaned")
        finally:
            db.close()

    response = await call_next(request)
    return response


@app.middleware("http")
async def private_network_access_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
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

# ── Scheduled jobs ───────────────────────────────────────────────────────────
# NEW — registered at module level so it runs under both `python main.py`
# and `uvicorn main:app` (a command-line uvicorn run never executes code
# inside `if __name__ == "__main__":`).
scheduler = AsyncIOScheduler()


async def _run_reminder_job():
    db = SessionLocal()
    try:
        await send_pending_letter_reminders(db)
    finally:
        db.close()


@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(_run_reminder_job, "cron", hour=8, minute=0)  # daily at 08:00
    scheduler.start()
    logger.info("Reminder scheduler started")


@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown(wait=False)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_config=None)