import asyncio

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.routes import admin, payments, webhooks
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.tasks.monitor import poll_tron


app = FastAPI(title=settings.app_name)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


if settings.https_only:
    @app.middleware("http")
    async def enforce_https(request: Request, call_next):
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if request.url.scheme != "https" and forwarded_proto != "https":
            return JSONResponse({"detail": "HTTPS required"}, status_code=400)
        return await call_next(request)


app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(webhooks.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(poll_tron())
