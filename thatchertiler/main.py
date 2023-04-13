"""ThatcherTiler application."""

from typing import Any, Dict, List

import jinja2
from aiopmtiles import Reader
from fastapi import FastAPI, Path, Query
from pmtiles.tile import Compression
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

from thatchertiler.model import StyleJSON, TileJSON

templates = Jinja2Templates(
    directory="",
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)

app = FastAPI(
    title="ThatcherTiler",
    description="""

<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/10407788/231709578-04c9ae59-c264-4319-be9d-a70d1bd98a1f.jpg"/>
  <p align="center">ThatcherTiler: expect some features to be dropped.</p>
</p>


**Source Code**: <a href="https://github.com/developmentseed/thatchertiler" target="_blank">https://github.com/developmentseed/thatchertiler</a>

    """,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/metadata")
async def metadata(url: str = Query(..., description="PMTiles archive URL.")):
    """get Metadata."""
    async with Reader(url) as src:
        return await src.metadata()


@app.get("/tiles/{z}/{x}/{y}", response_class=Response)
async def tiles(
    z: int = Path(ge=0, le=30, description="TMS tiles's zoom level"),
    x: int = Path(description="TMS tiles's column"),
    y: int = Path(description="TMS tiles's row"),
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get Tile."""
    headers: Dict[str, str] = {}

    async with Reader(url) as src:
        data = await src.get_tile(z, x, y)
        if src.tile_compression != Compression.NONE:
            headers["Content-Encoding"] = src.tile_compression.name.lower()

    return Response(data, media_type="application/x-protobuf", headers=headers)


@app.get(
    "/tilejson.json",
    response_model=TileJSON,
    response_model_exclude_none=True,
)
async def tilejson(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get TileJSON."""
    async with Reader(url) as src:
        meta = await src.metadata()

        tilejson = {
            "name": "pmtiles",
            "version": "1.0.0",
            "scheme": "xyz",
            "tiles": [
                str(request.url_for("tiles", z="{z}", x="{x}", y="{y}")) + f"?url={url}"
            ],
            "minzoom": src.minzoom,
            "maxzoom": src.maxzoom,
            "bounds": src.bounds,
            "center": src.center,
        }

        if vector_layers := meta.get("vector_layers"):
            tilejson["vector_layers"] = vector_layers

    return tilejson


@app.get(
    "/style.json",
    response_model=StyleJSON,
    response_model_exclude_none=True,
)
async def stylejson(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get StyleJSON."""
    tiles_url = str(request.url_for("tiles", z="{z}", x="{x}", y="{y}")) + f"?url={url}"

    style_json: Dict[str, Any]
    async with Reader(url) as src:
        if src.is_vector:
            style_json = {
                "sources": {
                    "pmtiles": {
                        "type": "vector",
                        "scheme": "xyz",
                        "tiles": [tiles_url],
                        "minzoom": src.minzoom,
                        "maxzoom": src.maxzoom,
                        "bounds": src.bounds,
                    },
                    "basemap": {
                        "type": "raster",
                        "tiles": [
                            "https://stamen-tiles-a.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-b.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-c.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-d.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                        ],
                        "tileSize": 256,
                        "attribution": 'Map tiles by <a href="https://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
                    },
                },
            }

            layers: List[Dict[str, Any]] = [
                {
                    "id": "basemap",
                    "type": "raster",
                    "source": "basemap",
                    "minzoom": 0,
                    "maxzoom": 20,
                }
            ]

            meta = await src.metadata()
            if vector_layers := meta.get("vector_layers"):
                for layer in vector_layers:
                    layer_id = layer["id"]
                    if layer_id == "mask":
                        layers.append(
                            {
                                "id": f"{layer_id}_fill",
                                "type": "fill",
                                "source": "pmtiles",
                                "source-layer": layer_id,
                                "filter": ["==", ["geometry-type"], "Polygon"],
                                "paint": {"fill-color": "black", "fill-opacity": 0.8},
                            }
                        )

                    else:
                        layers.append(
                            {
                                "id": f"{layer_id}_fill",
                                "type": "fill",
                                "source": "pmtiles",
                                "source-layer": layer_id,
                                "filter": ["==", ["geometry-type"], "Polygon"],
                                "paint": {
                                    "fill-color": "rgba(200, 100, 240, 0.4)",
                                    "fill-outline-color": "#000",
                                },
                            }
                        )

                    layers.append(
                        {
                            "id": f"{layer_id}_stroke",
                            "source": "pmtiles",
                            "source-layer": layer_id,
                            "type": "line",
                            "filter": ["==", ["geometry-type"], "LineString"],
                            "paint": {
                                "line-color": "#000",
                                "line-width": 1,
                                "line-opacity": 0.75,
                            },
                        }
                    )
                    layers.append(
                        {
                            "id": f"{layer_id}_point",
                            "source": "pmtiles",
                            "source-layer": layer_id,
                            "type": "circle",
                            "filter": ["==", ["geometry-type"], "Point"],
                            "paint": {
                                "circle-color": "#000",
                                "circle-radius": 2.5,
                                "circle-opacity": 0.75,
                            },
                        }
                    )

            style_json["layers"] = layers

        else:
            style_json = {
                "sources": {
                    "pmtiles": {
                        "type": "raster",
                        "scheme": "xyz",
                        "tiles": [tiles_url],
                        "minzoom": src.minzoom,
                        "maxzoom": src.maxzoom,
                        "bounds": src.bounds,
                    },
                    "basemap": {
                        "type": "raster",
                        "tiles": [
                            "https://stamen-tiles-a.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-b.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-c.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                            "https://stamen-tiles-d.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png",
                        ],
                        "tileSize": 256,
                        "attribution": 'Map tiles by <a href="https://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
                    },
                },
                "layers": [
                    {
                        "id": "basemap",
                        "type": "raster",
                        "source": "basemap",
                        "minzoom": 0,
                        "maxzoom": 20,
                    },
                    {
                        "id": "raster",
                        "type": "raster",
                        "source": "pmtiles",
                    },
                ],
            }
        style_json["center"] = [src.center[0], src.center[1]]
        style_json["zoom"] = src.center[2]

    return style_json


@app.get("/index.html", response_class=HTMLResponse)
async def viewer(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """Handle /index.html."""
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "style_endpoint": str(request.url_for("stylejson")) + f"?url={url}",
        },
        media_type="text/html",
    )
