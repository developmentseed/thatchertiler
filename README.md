## ThatcherTiler

<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/10407788/231709578-04c9ae59-c264-4319-be9d-a70d1bd98a1f.jpg"/>
  <p align="center">ThatcherTiler: expect some features to be dropped.</p>
</p>


---

**Documentation**:

**Source Code**: <a href="https://github.com/developmentseed/thatchertiler" target="_blank">https://github.com/developmentseed/thatchertiler</a>

---

`ThatcherTiler`* is a lightweight Raster/Vector tiles server based on the great [**PM**Tiles](https://github.com/protomaps/PMTiles) *Cloud-optimized + compressed single-file tile archives for vector and raster maps*.

While the original idea behind *PMTiles* is to create a single file which can be accessed directly from map client (e.g https://protomaps.com/docs/frontends/maplibre) some map client yet do not support it (e.g `Mapbox`) while a need for a `tile server` between the map client and the archive.

`ThatcherTiler` is a **DEMO** project to showcase the use of [aiopmtiles](https://github.com/developmentseed/aiopmtiles).


## Install

```bash
python -m pip install pip -U
git clone https://github.com/developmentseed/thatchertiler.git
cd thatchertiler
python -m pip install -e ".[server]"
```

## Launch

```bash
uvicorn thatchertiler.main:app --port 8080 --reload

>> INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

`http://127.0.0.1:8080/api.html`

![](https://user-images.githubusercontent.com/10407788/231717328-6d0608fa-145b-480e-ba48-629b0e4e3e97.png)


`http://127.0.0.1:8080/map?url=https://protomaps.github.io/PMTiles/protomaps(vector)ODbL_firenze.pmtiles`

![](https://user-images.githubusercontent.com/10407788/231720737-87cf14a9-35b3-4451-a183-37b80dc16e93.png)

## License

See [LICENSE](https://github.com/developmentseed/thatchertiler/blob/main/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

*`ThatcherTiler` name comes from a long a intense debate among @nerik, @kamicut, @batpad and @vincentsarago to find the better of the worse name. `Thatcher` is a reference to [`Margaret Thatcher`](https://fr.wikipedia.org/wiki/Margaret_Thatcher) which was once **P**rime **M**inister of the United Kingdom.
