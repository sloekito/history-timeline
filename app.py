import bisect

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from boundaries import boundary_for_event
from data import CHAOS_PERIODS, DYNASTY_COLORS, EVENTS, LEADERS, TERRITORY


def fmt_year(year):
    return f"{abs(year)} BCE" if year < 0 else f"{year} CE"


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
    "Click an event on the left to see the story behind it and Rome's approximate territorial "
    "shape at the time. The leaders column on the right lines up by year, so you can see who was "
    "in charge at that moment. ⭐ marks the \"Five Good Emperors,\" who each chose their successor "
    "rather than relying on bloodline. Boxed periods were chaotic multi-claimant stretches."
)

# Build a shared, non-linear year-to-display-position mapping used by both
# the events and leaders charts, so they stay aligned. Every gap between two
# consecutive "critical years" (an event, or a leader/chaos-period boundary)
# is clamped: never smaller than MIN_GAP (so tightly clustered labels, like
# Caesar's assassination-era events, never collide) and never larger than
# MAX_GAP (so centuries-long quiet stretches don't dominate the chart).
MIN_GAP = 6
MAX_GAP = 50

_critical_years = sorted(set(
    [int(e["year"]) for e in EVENTS]
    + [y for l in LEADERS for y in (l["start_year"], l["end_year"])]
    + [y for c in CHAOS_PERIODS for y in (c["start_year"], c["end_year"])]
))

_warped_positions = [0]
for _a, _b in zip(_critical_years, _critical_years[1:]):
    _adjusted_gap = min(max(_b - _a, MIN_GAP), MAX_GAP)
    _warped_positions.append(_warped_positions[-1] + _adjusted_gap)


def display_pos(year):
    """Map a real year to its warped display position via interpolation
    between the nearest bracketing critical years."""
    year = int(year)
    if year <= _critical_years[0]:
        return float(_warped_positions[0])
    if year >= _critical_years[-1]:
        return float(_warped_positions[-1])
    i = bisect.bisect_right(_critical_years, year) - 1
    y0, y1 = _critical_years[i], _critical_years[i + 1]
    p0, p1 = _warped_positions[i], _warped_positions[i + 1]
    t = (year - y0) / (y1 - y0)
    return p0 + t * (p1 - p0)


TOTAL_DISPLAY_HEIGHT = _warped_positions[-1]
Y_PAD = 10
SHARED_Y_RANGE = [TOTAL_DISPLAY_HEIGHT + Y_PAD, -Y_PAD]
CHART_HEIGHT = 4300

events_col, leaders_col, detail_col = st.columns([2, 2, 3], gap="small")

with events_col:
    df["display_y"] = df["year"].apply(display_pos)

    events_fig = go.Figure(
        go.Scatter(
            y=df["display_y"],
            x=[0] * len(df),
            mode="markers",
            marker=dict(size=22, color=EVENT_COLOR, opacity=0.18),
            customdata=df.index,
            hovertext=df.apply(lambda r: f"<b>{r['title']}</b><br>{r['display_date']}", axis=1),
            hoverinfo="text",
            showlegend=False,
        )
    )
    for _, r in df.iterrows():
        events_fig.add_annotation(
            x=0, y=r["display_y"], text=r["icon"], showarrow=False,
            xanchor="center", yanchor="middle", font=dict(size=14),
        )
        events_fig.add_annotation(
            x=0.35, y=r["display_y"],
            text=f"<b>{r['title']}</b>  <span style='font-size:9px;color:#777'>{r['display_date']}</span>",
            showarrow=False, xanchor="left", yanchor="middle", align="left",
            font=dict(size=11, color="#333333"), width=200,
        )
    events_fig.update_xaxes(visible=False, range=[-0.3, 3])
    events_fig.update_yaxes(visible=False, range=SHARED_Y_RANGE)
    events_fig.update_layout(
        height=CHART_HEIGHT,
        hovermode="closest",
        margin=dict(l=0, r=0, t=10, b=10),
    )
    event = st.plotly_chart(
        events_fig,
        width="stretch",
        on_select="rerun",
        selection_mode="points",
        key="timeline",
    )

with leaders_col:
    timeline_entries = [{**leader, "kind": "leader"} for leader in LEADERS]
    timeline_entries += [{**chaos, "kind": "chaos"} for chaos in CHAOS_PERIODS]

    BAR_X0, BAR_X1 = 0, 0.15
    LABEL_X = 0.22

    leaders_fig = go.Figure()

    for entry in timeline_entries:
        y0, y1 = display_pos(entry["start_year"]), display_pos(entry["end_year"])
        y_mid = (y0 + y1) / 2

        if entry["kind"] == "leader":
            color = DYNASTY_COLORS.get(entry["dynasty"], "#999999")
            leaders_fig.add_shape(type="rect", x0=BAR_X0, x1=BAR_X1, y0=y0, y1=y1, fillcolor=color, line=dict(width=0))
            star = "⭐ " if entry["five_good_emperors"] else ""
            label = f"{star}<b>{entry['name']}</b>  <span style='font-size:10px;color:#777'>{fmt_year(entry['start_year'])}–{fmt_year(entry['end_year'])}</span>"
            leaders_fig.add_annotation(
                x=LABEL_X, y=y_mid, text=label, showarrow=False,
                xanchor="left", yanchor="middle", align="left",
                font=dict(size=12, color="#8a6d00" if entry["five_good_emperors"] else "#333333"),
            )
        else:
            leaders_fig.add_shape(
                type="rect", x0=BAR_X0, x1=BAR_X1, y0=y0, y1=y1,
                fillcolor="#a63d3d", opacity=0.55, line=dict(width=0),
            )
            names_text = "<br>".join(entry["names"])
            label = (
                f"<b>{entry['label']}</b> "
                f"<span style='font-size:10px;color:#777'>{fmt_year(entry['start_year'])}–{fmt_year(entry['end_year'])}</span>"
                f"<br><span style='font-size:10px'>{names_text}</span>"
            )
            leaders_fig.add_annotation(
                x=LABEL_X, y=y_mid, text=label, showarrow=False,
                xanchor="left", yanchor="middle", align="left",
                font=dict(size=11, color="#7a2e2e"),
                bordercolor="#a63d3d", borderwidth=1, borderpad=5, bgcolor="rgba(166,61,61,0.06)",
            )

    leaders_fig.update_xaxes(visible=False, range=[-0.02, 5.3])
    leaders_fig.update_yaxes(visible=False, range=SHARED_Y_RANGE)
    leaders_fig.update_layout(
        height=CHART_HEIGHT,
        margin=dict(l=0, r=0, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(leaders_fig, width="stretch", key="leaders")

with detail_col:
    all_selected = event.selection.points if event and event.selection else []
    selected_points = [p for p in all_selected if p.get("customdata") is not None]

    row = None

    if selected_points:
        row_index = selected_points[0]["customdata"]
        row = df.loc[row_index]
        icon_col, text_col = st.columns([1, 4])
        with icon_col:
            st.markdown(f"<div style='font-size:48px'>{row['icon']}</div>", unsafe_allow_html=True)
        with text_col:
            st.subheader(f"{row['title']} — {row['display_date']}")
        st.write(row["summary"])
        if row.get("leads_to"):
            st.markdown(f"→ *{row['leads_to']}*")

        boundary = boundary_for_event(int(row["year"]))
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
