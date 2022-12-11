"""The main module entrypoint"""

from fastapi import (
    FastAPI,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.openapi.utils import (
    get_openapi,
)
from functools import (
    lru_cache,
)
import logging
from typing import (
    Any,
    Dict,
)
import uvicorn

from app.auth import (
    router as auth_router,
)
from app.config import (
    settings,
)
from app.nfts import (
    router as nfts_router,
)
from app.utils import (
    engine,
)
from app.wallets import (
    router as wallets_router,
)

logger = logging.getLogger(__name__)


@lru_cache()
def get_app() -> FastAPI:
    """
    A method that creates, configures and returns a FastAPI app instance

    Return:
        FastAPI : a FastAPI app instance
    """
    app_settings = settings()
    if app_settings.DEBUG == "info":
        app = FastAPI(
            docs_url="/docs",
            redoc_url="/redocs",
            title="Moerphous Server",
            description="Moerphous's server.",
            version="3.0",
            openapi_url="/api/v1/openapi.json",
        )
    else:
        app = FastAPI(
            docs_url=None,
            redoc_url=None,
            title=None,
            description=None,
            version=None,
            openapi_url=None,
        )

    origins = [
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://localhost:3000",
    ]

    origins.extend(app_settings.cors_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup() -> None:
        logger.info("Connecting to MongoDB...")
        await engine.init_engine_app(app)
        logger.info("Connected to MongoDB!")

    @app.on_event("shutdown")
    async def shutdown() -> None:
        logger.info("Closing connection with MongoDB...")
        # bug: TypeError: object NoneType can't be used in 'await' expression
        try:
            await app.state.client.close()
        except Exception as err:
            logger.error(repr(err))
        logger.info("Closed connection with MongoDB!")

    @app.get("/api")
    async def root() -> Dict[str, str]:
        return {"message": "Welcome to Moerphous's Server."}

    app.include_router(auth_router.router, tags=["auth"])
    app.include_router(wallets_router.router, tags=["wallets"])
    app.include_router(nfts_router.router, tags=["nfts"])

    # change openapi auth method to bearer token instead of user and password
    def custom_openapi() -> Any:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Moerphous Server",
            version="3.0",
            description="Moerphous's server APIs.",
            routes=app.routes,
        )

        openapi_schema["components"]["securitySchemes"]["JWT"]["type"] = "http"
        openapi_schema["components"]["securitySchemes"]["JWT"]["scheme"] = "bearer"
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app


tinder_app = get_app()


def serve() -> None:
    """
    A method that run a uvicorn command.
    """
    try:

        uvicorn.run(
            "app.main:tinder_app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )
    except Exception as err:
        logger.error(repr(err))


if __name__ == "__main__":
    serve()
