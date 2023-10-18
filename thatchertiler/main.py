"""ThatcherTiler application."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from thatchertiler.factory import TilerFactory
from thatchertiler.settings import ApiSettings

settings = ApiSettings()


app = FastAPI(
    title="ThatcherTiler",
    openapi_url="/api",
    docs_url="/api.html",
    root_path=settings.root_path,
    description="""

<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/10407788/231709578-04c9ae59-c264-4319-be9d-a70d1bd98a1f.jpg"/>
  <p align="center">ThatcherTiler: expect some features to be dropped.</p>
</p>


**Source Code**: <a href="https://github.com/developmentseed/thatchertiler" target="_blank">https://github.com/developmentseed/thatchertiler</a>

    """,
)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

tiler = TilerFactory(with_map=True, with_wmts=True)
app.include_router(tiler.router, tags=["PMTiles"])


@app.get(
    "/healthz",
    description="Health Check.",
    summary="Health Check.",
    operation_id="healthCheck",
    tags=["Health Check"],
)
def ping():
    """Health check."""
    return {"ping": "pong!"}
