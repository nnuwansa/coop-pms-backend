from typing import Any, Optional

from pydantic import BaseModel


class GenericResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class GenericResponsePaginated(GenericResponse):
    total: int
    total_pages: int
    page: int
    page_size: int
