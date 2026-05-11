from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src.utils.config import AppConfig
from src.web.auth import CredentialStore, current_username, is_authenticated, login_session, logout_session
from src.web.schemas import detection_history_to_dto
from src.web.stream import LatestStateBuffer


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_state(request: Request) -> LatestStateBuffer:
    return request.app.state.latest_state


def get_storage(request: Request):
    return request.app.state.storage


def get_analysis_service(request: Request):
    return request.app.state.analysis_service


def get_chat_service(request: Request):
    return request.app.state.chat_service


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

    @router.get("/analysis", response_class=HTMLResponse)
    async def analysis_page(request: Request):
        if not is_authenticated(request):
            return login_redirect()
        return templates.TemplateResponse(
            request,
            "analysis.html",
            {"username": current_username(request), "active": "analysis"},
        )

    @router.get("/chat", response_class=HTMLResponse)
    async def chat_page(request: Request):
        if not is_authenticated(request):
            return login_redirect()
        return templates.TemplateResponse(
            request,
            "chat.html",
            {"username": current_username(request), "active": "chat"},
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

    @router.get("/api/detections/recent")
    async def recent_detections(
        request: Request,
        hours: int = 48,
        class_name: str | None = None,
        min_confidence: float | None = None,
    ):
        require_api_login(request)
        rows = get_storage(request).recent_detections(
            hours=hours,
            class_name=class_name,
            min_confidence=min_confidence,
        )
        return JSONResponse(
            {
                "hours": max(1, min(48, int(hours))),
                "detections": [detection_history_to_dto(row).to_dict() for row in rows],
            }
        )

    @router.get("/api/detections/{detection_id}")
    async def detection_detail(request: Request, detection_id: str):
        require_api_login(request)
        row = get_storage(request).detection_detail(detection_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Detection not found")
        return JSONResponse(detection_history_to_dto(row).to_dict())

    @router.post("/api/agent/analyze", status_code=202)
    async def start_analysis(request: Request):
        require_api_login(request)
        payload = await _json_or_empty(request)
        response = get_analysis_service(request).start_analysis(
            hours=int(payload.get("hours", 48)),
            trigger_type=str(payload.get("trigger_type", "manual")),
            crop_stage=payload.get("crop_stage"),
            environment=payload.get("environment"),
            async_run=True,
        )
        return JSONResponse(response, status_code=202)

    @router.get("/api/agent/analysis/recent")
    async def recent_analysis(request: Request, hours: int = 48):
        require_api_login(request)
        return JSONResponse({"hours": max(1, min(48, int(hours))), "analyses": get_analysis_service(request).recent(hours=hours)})

    @router.get("/api/agent/analysis/{analysis_id}")
    async def analysis_detail(request: Request, analysis_id: str):
        require_api_login(request)
        row = get_analysis_service(request).detail(analysis_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return JSONResponse(row)

    @router.post("/api/agent/chat")
    async def agent_chat(request: Request):
        require_api_login(request)
        payload = await request.json()
        question = str(payload.get("question", "")).strip()
        if not question:
            raise HTTPException(status_code=422, detail="question is required")
        return JSONResponse(
            get_chat_service(request).answer(
                user_id=current_username(request) or "unknown",
                question=question,
                language=str(payload.get("language", "zh")),
                hours=int(payload.get("hours", 48)),
            )
        )

    @router.get("/api/i18n/languages")
    async def languages(request: Request):
        return JSONResponse(request.app.state.i18n)

    return router


def _one_frame(frames):
    yield next(iter(frames))


async def _json_or_empty(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
