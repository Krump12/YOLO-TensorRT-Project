from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.utils.config import AppConfig
from src.web.routes import create_router
from src.web.stream import LatestStateBuffer, WebDetectionPipeline


WEB_DIR = Path(__file__).resolve().parent


def create_app(
    config: AppConfig,
    *,
    latest_state: LatestStateBuffer | None = None,
    pipeline: WebDetectionPipeline | None = None,
    start_pipeline: bool = True,
) -> FastAPI:
    config.web.password()
    session_secret = config.web.session_secret()
    state = latest_state or LatestStateBuffer()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime_pipeline = pipeline
        if start_pipeline:
            runtime_pipeline = runtime_pipeline or WebDetectionPipeline(config, state)
            app.state.pipeline = runtime_pipeline
            runtime_pipeline.start()
        try:
            yield
        finally:
            runtime_pipeline = getattr(app.state, "pipeline", None)
            if runtime_pipeline is not None:
                runtime_pipeline.stop()

    app = FastAPI(title="YOLO TensorRT Web Dashboard", lifespan=lifespan)
    app.state.config = config
    app.state.latest_state = state
    app.add_middleware(SessionMiddleware, secret_key=session_secret, same_site="lax")

    static_dir = WEB_DIR / "static"
    templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(create_router(templates))
    return app
