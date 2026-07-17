import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from boundaries import boundary_for_event
from data import EVENTS, TERRITORY


def _rings(geometry):
    """Yield exterior-ring [lon, lat] coordinate lists for a Polygon/MultiPolygon."""
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            yield polygon[0]


def interpolate_km2(year, years, kms):
    """Piecewise-linear interpolation of territory size at an arbitrary year."""
    if year <= years[0]:
        return kms[0]
    if year >= years[-1]:
        return kms[-1]
    for y0, y1, k0, k1 in zip(years, years[1:], kms, kms[1:]):
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0) if y1 != y0 else 0
            return k0 + t * (k1 - k0)
    return kms[-1]


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
    "Click an event to see the story behind it and Rome's approximate territorial "
    "shape at the time, then scroll down for the empire's full territorial arc."
)

events_fig = go.Figure(
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
    )
)
events_fig.update_yaxes(visible=False)
events_fig.update_xaxes(title_text="Year (negative = BCE)")
events_fig.update_layout(
    height=180,
    hovermode="closest",
    margin=dict(l=10, r=10, t=10, b=10),
)

event = st.plotly_chart(
    events_fig,
    width="stretch",
    on_select="rerun",
    selection_mode="points",
    key="timeline",
)

st.divider()

all_selected = event.selection.points if event and event.selection else []
selected_points = [p for p in all_selected if p.get("customdata") is not None]

row = None

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

st.divider()

st.subheader("Territorial Extent Over Time")
st.caption("Rome's approximate size in km² across its history. Figures are illustrative estimates.")

territory_fig = go.Figure(
    go.Scatter(
        x=territory_df["year"],
        y=territory_df["km2"],
        mode="lines",
        line=dict(color=TERRITORY_COLOR, width=2),
        fill="tozeroy",
        fillcolor="rgba(192, 57, 43, 0.15)",
        hovertext=territory_df.apply(lambda r: f"{r['km2']:,} km²<br>{r['note']}", axis=1),
        hoverinfo="text",
        showlegend=False,
    )
)
territory_fig.update_yaxes(title_text="Territory (km²)")
territory_fig.update_xaxes(title_text="Year (negative = BCE)")
territory_fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))

if row is not None:
    event_km2 = interpolate_km2(
        int(row["year"]), territory_df["year"].tolist(), territory_df["km2"].tolist()
    )
    territory_fig.add_trace(
        go.Scatter(
            x=[row["year"]],
            y=[event_km2],
            mode="markers+text",
            marker=dict(size=16, color=EVENT_COLOR, line=dict(color="white", width=2)),
            text=[row["icon"]],
            textposition="top center",
            hovertext=[f"<b>{row['title']}</b><br>{row['display_date']}<br>~{event_km2:,.0f} km²"],
            hoverinfo="text",
            showlegend=False,
        )
    )
    territory_fig.add_vline(x=row["year"], line_dash="dot", line_color=EVENT_COLOR, opacity=0.5)

st.plotly_chart(territory_fig, width="stretch", key="territory")
