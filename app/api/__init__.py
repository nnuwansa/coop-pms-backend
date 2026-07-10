from fastapi import APIRouter
from starlette.responses import HTMLResponse

from api.auth import router as auth_router
from api.department import router as department_router
from api.letter import router as letter_router
from api.organization import router as organization_router
from api.permission import router as permission_router
from api.role import router as role_router
from api.source import router as source_router
from api.status import router as status_router
from api.system_user import router as system_user_router
from api.designation import router as designation_router
from api.employee_name import router as employee_name_router

all_routers = APIRouter()
all_routers.include_router(letter_router)
all_routers.include_router(source_router)
all_routers.include_router(organization_router)
all_routers.include_router(department_router)
all_routers.include_router(designation_router)
all_routers.include_router(employee_name_router)
all_routers.include_router(status_router)
all_routers.include_router(system_user_router)
all_routers.include_router(role_router)
all_routers.include_router(permission_router)
all_routers.include_router(auth_router)


@all_routers.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>COOP PMS Core Service</title>
        </head>
        <body>
            <h1>Welcome to COOP Postal Management System Core Service !</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
