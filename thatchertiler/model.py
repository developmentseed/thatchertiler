"""response models."""

from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, root_validator


class SchemeEnum(str, Enum):
    """TileJSON scheme choice."""

    xyz = "xyz"
    tms = "tms"


class LayerJSON(BaseModel):
    """
    https://github.com/mapbox/tilejson-spec/tree/master/3.0.0#33-vector_layers
    """

    id: str
    fields: Dict = Field(default_factory=dict)
    description: Optional[str]
    minzoom: Optional[int]
    maxzoom: Optional[int]


class TileJSON(BaseModel):
    """
    TileJSON model.
    Based on https://github.com/mapbox/tilejson-spec/tree/master/2.2.0
    """

    tilejson: str = "3.0.0"
    name: Optional[str]
    description: Optional[str]
    version: str = "1.0.0"
    attribution: Optional[str]
    template: Optional[str]
    legend: Optional[str]
    scheme: SchemeEnum = SchemeEnum.xyz
    tiles: List[str]
    vector_layers: Optional[List[LayerJSON]]
    grids: Optional[List[str]]
    data: Optional[List[str]]
    minzoom: int = Field(0, ge=0, le=30)
    maxzoom: int = Field(30, ge=0, le=30)
    fillzoom: Optional[int]
    bounds: List[float] = [180, -85.05112877980659, 180, 85.0511287798066]
    center: Optional[Tuple[float, float, int]]

    @root_validator
    def compute_center(cls, values):
        """Compute center if it does not exist."""
        bounds = values["bounds"]
        if not values.get("center"):
            values["center"] = (
                (bounds[0] + bounds[2]) / 2,
                (bounds[1] + bounds[3]) / 2,
                values["minzoom"],
            )
        return values

    class Config:
        """TileJSON model configuration."""

        use_enum_values = True


class StyleJSON(BaseModel):
    """
    Simple Mapbox/Maplibre Style JSON model.

    Based on https://docs.mapbox.com/help/glossary/style/

    """

    version: int = 8
    name: Optional[str]
    metadata: Optional[Dict]
    layers: List[Dict]
    sources: Dict
    center: List[float]
    zoom: int
