"""Lookup of Roman territorial boundary shapes for a given event year.

Boundary polygons come from a trimmed extract of aourednik/historical-basemaps
(GPLv3), snapshotted at specific years. Since Rome's actual borders shifted
continuously, we show the nearest available snapshot rather than an exact
match - illustrative, not authoritative.
"""

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "geo_data" / "rome_boundaries.geojson"

with open(_DATA_PATH) as f:
    _GEOJSON = json.load(f)

# Years for which a boundary snapshot exists, sorted ascending.
BOUNDARY_YEARS = sorted({f["properties"]["period_year"] for f in _GEOJSON["features"]})

# The Western Roman Empire had no territory left after this point.
COLLAPSE_YEAR = 476
# Rome was too small a city-state to appear in world-scale maps before this.
EARLIEST_BOUNDARY_YEAR = min(BOUNDARY_YEARS)


def boundary_for_event(event_year: int):
    """Return (snapshot_year, label, [geometries]) for the nearest available
    boundary snapshot to `event_year`, or None if no territory should be shown.
    """
    if event_year >= COLLAPSE_YEAR or event_year < EARLIEST_BOUNDARY_YEAR:
        return None

    nearest_year = min(BOUNDARY_YEARS, key=lambda y: abs(y - event_year))
    features = [f for f in _GEOJSON["features"] if f["properties"]["period_year"] == nearest_year]
    label = features[0]["properties"]["label"]
    geometries = [f["geometry"] for f in features]
    return nearest_year, label, geometries
