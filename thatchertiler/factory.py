"""thatchertiler.factory."""

import abc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union
from urllib.parse import urlencode

import jinja2
from aiopmtiles import Reader
from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.params import Depends as DependsFunc
from pmtiles.tile import Compression
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Match, compile_path, replace_params
from starlette.templating import Jinja2Templates
from typing_extensions import Annotated

from thatchertiler.model import StyleJSON, TileJSON
from thatchertiler.routing import EndpointScope

DEFAULT_TEMPLATES = Jinja2Templates(
    directory="",
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")]),
)


@dataclass  # type: ignore
class FactoryExtension(metaclass=abc.ABCMeta):
    """Factory Extension."""

    @abc.abstractmethod
    def register(self, factory: "TilerFactory"):
        """Register extension to the factory."""
        ...


def PathParams(url: Annotated[str, Query(description="PMTiles archive URL.")]) -> str:
    """Dataset Parameter"""
    return url


@dataclass
class TilerFactory:
    """thatchertiler endpoint factory."""

    path_dependency: Callable[..., str] = PathParams

    # FastAPI router
    router: APIRouter = field(default_factory=APIRouter)

    # Router Prefix is needed to find the path for /tile if the TilerFactory.router is mounted
    # with other router (multiple `.../tile` routes).
    # e.g if you mount the route with `/cog` prefix, set router_prefix to cog and
    router_prefix: str = ""

    # add dependencies to specific routes
    route_dependencies: List[Tuple[List[EndpointScope], List[DependsFunc]]] = field(
        default_factory=list
    )

    extensions: List[FactoryExtension] = field(default_factory=list)

    templates: Jinja2Templates = DEFAULT_TEMPLATES

    def __post_init__(self):
        """Post Init: register route and configure specific options."""
        # Register endpoints
        self.register_routes()

        # Register Extensions
        for ext in self.extensions:
            ext.register(self)

        # Update endpoints dependencies
        for scopes, dependencies in self.route_dependencies:
            self.add_route_dependencies(scopes=scopes, dependencies=dependencies)

    def url_for(self, request: Request, name: str, **path_params: Any) -> str:
        """Return full url (with prefix) for a specific endpoint."""
        url_path = self.router.url_path_for(name, **path_params)
        base_url = str(request.base_url)
        if self.router_prefix:
            prefix = self.router_prefix.lstrip("/")
            # If we have prefix with custom path param we check and replace them with
            # the path params provided
            if "{" in prefix:
                _, path_format, param_convertors = compile_path(prefix)
                prefix, _ = replace_params(
                    path_format, param_convertors, request.path_params.copy()
                )
            base_url += prefix

        return str(url_path.make_absolute_url(base_url=base_url))

    def add_route_dependencies(
        self,
        *,
        scopes: List[EndpointScope],
        dependencies=List[DependsFunc],
    ):
        """Add dependencies to routes.

        Allows a developer to add dependencies to a route after the route has been defined.

        """
        for route in self.router.routes:
            for scope in scopes:
                match, _ = route.matches({"type": "http", **scope})  # type: ignore
                if match != Match.FULL:
                    continue

                # Mimicking how APIRoute handles dependencies:
                # https://github.com/tiangolo/fastapi/blob/1760da0efa55585c19835d81afa8ca386036c325/fastapi/routing.py#L408-L412
                for depends in dependencies[::-1]:
                    route.dependant.dependencies.insert(  # type: ignore
                        0,
                        get_parameterless_sub_dependant(
                            depends=depends, path=route.path_format  # type: ignore
                        ),
                    )

                # Register dependencies directly on route so that they aren't ignored if
                # the routes are later associated with an app (e.g. app.include_router(router))
                # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/applications.py#L337-L360
                # https://github.com/tiangolo/fastapi/blob/58ab733f19846b4875c5b79bfb1f4d1cb7f4823f/fastapi/routing.py#L677-L678
                route.dependencies.extend(dependencies)  # type: ignore

    def register_routes(self):
        """Register Tiler Routes."""

        self._register_metadata()
        self._register_tiles()
        self._register_style()
        self._register_map()

    def _register_metadata(self):
        """register /metadata endpoint."""

        @self.router.get("/metadata")
        async def metadata(dataset=Depends(self.path_dependency)):
            """get PMTiles Metadata."""
            async with Reader(dataset) as src:
                return await src.metadata()

    def _register_tiles(self):
        """register /tiles and /tilejson.json endpoints."""

        @self.router.get("/tiles/{z}/{x}/{y}", response_class=Response)
        async def tiles_endpoint(
            z: Annotated[int, Path(ge=0, le=30, description="TMS tiles's zoom level")],
            x: Annotated[int, Path(description="TMS tiles's column")],
            y: Annotated[int, Path(description="TMS tiles's row")],
            dataset=Depends(self.path_dependency),
        ):
            """get Tile."""
            headers: Dict[str, str] = {}

            async with Reader(dataset) as src:
                data = await src.get_tile(z, x, y)
                if src.tile_compression != Compression.NONE:
                    headers["Content-Encoding"] = src.tile_compression.name.lower()

            return Response(data, media_type="application/x-protobuf", headers=headers)

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            response_model_exclude_none=True,
        )
        async def tilejson_endpoint(
            request: Request, dataset=Depends(self.path_dependency)
        ):
            """get TileJSON."""
            async with Reader(dataset) as src:
                meta = await src.metadata()

                route_params = {
                    "z": "{z}",
                    "x": "{x}",
                    "y": "{y}",
                }
                tiles_url = self.url_for(request, "tiles_endpoint", **route_params)

                if request.query_params._list:
                    tiles_url += f"?{urlencode(request.query_params._list)}"

                tilejson = {
                    "name": "pmtiles",
                    "version": "1.0.0",
                    "scheme": "xyz",
                    "tiles": [tiles_url],
                    "minzoom": src.minzoom,
                    "maxzoom": src.maxzoom,
                    "bounds": src.bounds,
                    "center": src.center,
                }

                if vector_layers := meta.get("vector_layers"):
                    tilejson["vector_layers"] = vector_layers

            return tilejson

    def _register_style(self):
        """register /style.json endpoint."""

        @self.router.get(
            "/style.json",
            response_model=StyleJSON,
            response_model_exclude_none=True,
        )
        async def stylejson_endpoint(
            request: Request, dataset=Depends(self.path_dependency)
        ):
            """get StyleJSON."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
            }
            tiles_url = self.url_for(request, "tiles_endpoint", **route_params)

            if request.query_params._list:
                tiles_url += f"?{urlencode(request.query_params._list)}"

            style_json: Dict[str, Any]
            async with Reader(dataset) as src:
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
                                    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                ],
                                "tileSize": 256,
                                "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
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
                                        "paint": {
                                            "fill-color": "black",
                                            "fill-opacity": 0.8,
                                        },
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
                                    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                ],
                                "tileSize": 256,
                                "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
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

    def _register_map(self):
        """add /map endpoint."""

        @self.router.get("/map", response_class=HTMLResponse)
        async def map_endpoint(request: Request, dataset=Depends(self.path_dependency)):
            """Handle /index.html."""
            stylejson_url = self.url_for(request, "stylejson_endpoint")
            if request.query_params._list:
                stylejson_url += f"?{urlencode(request.query_params._list)}"

            return self.templates.TemplateResponse(
                name="index.html",
                context={
                    "request": request,
                    "style_endpoint": stylejson_url,
                },
                media_type="text/html",
            )
