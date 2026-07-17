import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from boundaries import boundary_for_event
from data import EVENTS, TERRITORY


def _rings(geometry):
    """Yield exterior-ring [lon, lat] coordinate lists for a Polygon/MultiPolygon."""
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield polygon[0]


def render_boundary_map(geometries):
    fig = go.Figure()
    for geometry in geometries:
        for ring in _rings(geometry):
            fig.add_trace(
                go.Scattergeo(
                    lon=[pt[0] for pt in ring],
                    lat=[pt[1] for pt in ring],
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(192, 57, 43, 0.45)",
                    line=dict(color="#c0392b", width=1),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
    fig.update_geos(
        projection_type="natural earth",
        lataxis_range=[10, 60],
        lonaxis_range=[-15, 55],
        showcountries=False,
        showland=True,
        landcolor="#f0ead6",
        showocean=True,
        oceancolor="#dbe9f4",
        showlakes=False,
        showframe=False,
    )
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=0, b=0))
    return fig

st.set_page_config(page_title="Rise and Fall of Rome", layout="wide")

df = pd.DataFrame(EVENTS).sort_values("year").reset_index(drop=True)
territory_df = pd.DataFrame(TERRITORY).sort_values("year").reset_index(drop=True)

EVENT_COLOR = "#c0392b"
TERRITORY_COLOR = "#8e2f22"

st.title("Rise and Fall of Rome")
st.caption(
    "Character-driven events (top) plotted against Rome's approximate territorial "
    "extent over time (bottom, in km²). Territorial figures are illustrative estimates."
)

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.25, 0.75],
    vertical_spacing=0.03,
)

fig.add_trace(
    go.Scatter(
        x=df["year"],
        y=[0] * len(df),
        mode="markers+text",
        marker=dict(size=30, color=EVENT_COLOR, opacity=0.18),
        text=df["icon"],
        textfont=dict(size=18),
        textposition="middle center",
        customdata=df.index,
        hovertext=df.apply(lambda r: f"<b>{r['title']}</b><br>{r['display_date']}", axis=1),
        hoverinfo="text",
        showlegend=False,
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=territory_df["year"],
        y=territory_df["km2"],
        mode="lines",
        line=dict(color=TERRITORY_COLOR, width=2),
        fill="tozeroy",
        fillcolor="rgba(192, 57, 43, 0.15)",
        hovertext=territory_df.apply(
            lambda r: f"{r['km2']:,} km²<br>{r['note']}", axis=1
        ),
        hoverinfo="text",
        showlegend=False,
    ),
    row=2,
    col=1,
)

fig.update_yaxes(visible=False, row=1, col=1)
fig.update_yaxes(title_text="Territory (km²)", row=2, col=1)
fig.update_xaxes(title_text="Year (negative = BCE)", row=2, col=1)

fig.update_layout(
    height=550,
    hovermode="closest",
    margin=dict(l=10, r=10, t=10, b=10),
)

event = st.plotly_chart(
    fig,
    width="stretch",
    on_select="rerun",
    selection_mode="points",
    key="timeline",
)

st.divider()

all_selected = event.selection.points if event and event.selection else []
selected_points = [p for p in all_selected if p.get("customdata") is not None]

if selected_points:
    row_index = selected_points[0]["customdata"]
    row = df.loc[row_index]
    icon_col, text_col = st.columns([1, 6])
    with icon_col:
        st.markdown(f"<div style='font-size:64px'>{row['icon']}</div>", unsafe_allow_html=True)
    with text_col:
        st.subheader(f"{row['title']} — {row['display_date']}")
        st.write(row["summary"])
        if row.get("leads_to"):
            st.markdown(f"→ *{row['leads_to']}*")

    boundary = boundary_for_event(int(row["year"]))
    map_col, _ = st.columns([2, 1])
    with map_col:
        if boundary:
            snapshot_year, label, geometries = boundary
            snapshot_display = f"{abs(snapshot_year)} BCE" if snapshot_year < 0 else f"{snapshot_year} CE"
            st.caption(f"Rome's approximate extent, nearest snapshot: {label}, {snapshot_display}")
            st.plotly_chart(render_boundary_map(geometries), width="stretch", key=f"map-{row_index}")
        elif int(row["year"]) >= 476:
            st.caption("By this point, the Western Roman Empire has already collapsed - no territory left to show.")
        else:
            st.caption("Rome is still just a small city here - too small to appear on a world map yet.")
else:
    st.info("Click an event on the timeline to see details.")
