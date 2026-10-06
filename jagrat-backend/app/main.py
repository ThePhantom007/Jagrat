from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import health, profile, journal, mentor, actions, growth, reports, teachings, history, journey, honesty, features


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.bootstrap import bootstrap
    bootstrap()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(health.router)
for router in [profile.router, journal.router, features.router, mentor.router, actions.router, growth.router, reports.router, teachings.router, history.router, journey.router, honesty.router]:
    app.include_router(router, prefix="/api")
