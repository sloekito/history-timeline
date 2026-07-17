# Rise and Fall of Rome

An interactive, character-led timeline of Roman history - built to make history less boring.

**Live app:** https://history-timeline.streamlit.app/

## What it does

- **Event timeline** - click through Roman history from the founding of the city (753 BCE) to
  medieval proverbs still said about it (1190 CE), told through the people and moments most likely to
  ring a bell: Caesar, Cleopatra, Spartacus, Nero, famous sayings like *"Carthago delenda est"* and
  *"veni, vidi, vici"*. Each event's detail card includes a `leads_to` line connecting it to what it
  set in motion, so browsing chronologically reads as a narrative rather than a trivia list.
- **Territorial extent chart** - a filled area chart of Rome's approximate size (km²) over the same
  timeline, so you can see events in the context of whether the empire was still rising, at its peak,
  or already in decline.
- **Boundary map** - clicking an event also renders Rome's approximate territorial shape at (or near)
  that point in history on an actual map.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

- [`data.py`](data.py) - the event list (`EVENTS`) and territorial-extent milestones (`TERRITORY`).
  Each event needs a `title`, a `year` (astronomical numbering - BCE years are negative, e.g.
  `753 BCE` -> `-753`), a `display_date` string, a `category`, an `icon` emoji, a `summary`, and a
  `leads_to` bridge sentence.
- [`boundaries.py`](boundaries.py) - looks up the nearest available territorial boundary snapshot for
  a given event year.
- [`geo_data/rome_boundaries.geojson`](geo_data/rome_boundaries.geojson) - trimmed boundary polygons
  for Rome at ten snapshot years (500 BCE - 400 CE).
- [`app.py`](app.py) - the Streamlit app itself.

## Data sources and caveats

- Territorial extent (km²) and boundary shapes are **illustrative estimates**, not precise historical
  measurements - ancient territorial figures are genuinely disputed among historians.
- Boundary snapshots are roughly a century apart, so the map shown for a given event is the *nearest
  available year*, not that exact date. After the Western Roman Empire's collapse (476 CE), no
  territory is shown.
- Boundary polygons are a trimmed extract from
  [aourednik/historical-basemaps](https://github.com/aourednik/historical-basemaps), used under
  GPLv3.
