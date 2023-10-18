"""test endpoints."""

import os

import pytest

datasets = [
    "protomaps(vector)ODbL_firenze.pmtiles",
    "stamen_toner(raster)CC-BY_ODbL_z3.pmtiles",
    "usgs-mt-whitney-8-15-webp-512.pmtiles",
]


@pytest.mark.parametrize("dataset", datasets)
def test_metadata(app, data_dir, dataset):
    """test /metadata endpoint"""
    response = app.get(f"/metadata?url={os.path.join(data_dir, dataset)}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize("dataset", datasets)
def test_tilejson(app, data_dir, dataset):
    """test /tilejson endpoint"""
    response = app.get(f"/tilejson.json?url={os.path.join(data_dir, dataset)}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize("dataset", datasets)
def test_stylejson(app, data_dir, dataset):
    """test /style.json endpoint"""
    response = app.get(f"/style.json?url={os.path.join(data_dir, dataset)}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize("dataset", datasets)
def test_map(app, data_dir, dataset):
    """test /map endpoint"""
    response = app.get(f"/map?url={os.path.join(data_dir, dataset)}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("dataset", datasets)
def test_wmts(app, data_dir, dataset):
    """test /wmts endpoint"""
    response = app.get(f"/WMTSCapabilities.xml?url={os.path.join(data_dir, dataset)}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
