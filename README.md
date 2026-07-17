# Historical Timeline

An interactive, visual timeline of major historical events - built to make history less boring.

**Live app:** https://history-timeline.streamlit.app/

## What it does

Click through a Plotly-powered timeline spanning ancient Rome to the present day. Events are grouped
into swimlanes by category, each marked with an icon, and clicking any event opens a detail card with
context and the story behind it.

Categories:
- **Rome** - the Republic and Empire, from Romulus and Remus to famous Latin sayings like *"Carthago
  delenda est"* and *"Veni, vidi, vici"*
- **Istanbul** - Constantinople/Byzantium/Istanbul across its Roman, Byzantine, and Ottoman chapters
- **World History** - the events most people have heard of, from the Black Death to 9/11

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Adding events

Events live in [`data.py`](data.py) as a plain list of dicts. Each entry needs a `title`, a `year`
(astronomical numbering - BCE years are negative, e.g. `753 BCE` -> `-753`), a `display_date` string
for display, a `category`, an `icon` emoji, and a `summary`.
