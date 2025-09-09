import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.settings import settings

docs_routes = APIRouter()
security = HTTPBasic()


def docs_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> bool:
    ok_user = secrets.compare_digest(credentials.username, settings.documentation_username)
    ok_pass = secrets.compare_digest(credentials.password, settings.documentation_password)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


@docs_routes.get(settings.openapi_url, include_in_schema=False)
async def protected_openapi(request: Request, _: Annotated[bool, Depends(docs_auth)]) -> JSONResponse:
    app = request.app
    if getattr(app, "openapi_schema", None):
        return JSONResponse(app.openapi_schema)
    schema = get_openapi(
        title=app.title,
        version=getattr(app, "version", "0.1.0"),
        description=getattr(app, "description", None),
        routes=app.routes,
    )
    app.openapi_schema = schema
    return JSONResponse(schema)


@docs_routes.get("/docs", include_in_schema=False)
async def protected_swagger(_: Annotated[bool, Depends(docs_auth)]) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url=settings.openapi_url, title=f"{settings.app_title} Swagger UI")


@docs_routes.get("/redoc", include_in_schema=False)
async def protected_redoc(_: Annotated[bool, Depends(docs_auth)]) -> HTMLResponse:
    return get_redoc_html(openapi_url=settings.openapi_url, title=f"{settings.app_title} ReDoc")
