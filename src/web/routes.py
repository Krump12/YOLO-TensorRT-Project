from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src.utils.config import AppConfig
from src.web.auth import CredentialStore, current_username, is_authenticated, login_session, logout_session
from src.web.stream import LatestStateBuffer


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_state(request: Request) -> LatestStateBuffer:
    return request.app.state.latest_state


def require_api_login(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


def login_redirect() -> RedirectResponse:
    return RedirectResponse("/login", status_code=302)


def create_router(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", include_in_schema=False)
    async def root(request: Request):
        if is_authenticated(request):
            return RedirectResponse("/dashboard", status_code=302)
        return login_redirect()

    @router.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        if is_authenticated(request):
            return RedirectResponse("/dashboard", status_code=302)
        return templates.TemplateResponse(request, "login.html", {"error": ""})

    @router.post("/login")
    async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
        credentials = CredentialStore.from_config(get_config(request).web)
        if not credentials.verify(username, password):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "Invalid username or password"},
                status_code=401,
            )
        login_session(request, username)
        return RedirectResponse("/dashboard", status_code=302)

    @router.post("/logout")
    async def logout(request: Request):
        logout_session(request)
        return RedirectResponse("/login", status_code=302)

    @router.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request):
        if not is_authenticated(request):
            return login_redirect()
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"username": current_username(request), "active": "dashboard"},
        )

    @router.get("/detections", response_class=HTMLResponse)
    async def detections_page(request: Request):
        if not is_authenticated(request):
            return login_redirect()
        return templates.TemplateResponse(
            request,
            "detections.html",
            {"username": current_username(request), "active": "detections"},
        )

    @router.get("/video_feed")
    async def video_feed(request: Request, once: bool = False):
        if not is_authenticated(request):
            return login_redirect()
        config = get_config(request)
        state = get_state(request)
        frames = state.mjpeg_frames(config.web.stream_fps)
        if once:
            frames = _one_frame(frames)
        return StreamingResponse(
            frames,
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    @router.get("/api/detections/latest")
    async def latest_detections(request: Request):
        require_api_login(request)
        return JSONResponse(get_state(request).latest_detections().to_dict())

    @router.get("/api/status")
    async def status(request: Request):
        require_api_login(request)
        return JSONResponse(get_state(request).status().to_dict())

    return router


def _one_frame(frames):
    yield next(iter(frames))
