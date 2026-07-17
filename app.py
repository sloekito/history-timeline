import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import EVENTS

st.set_page_config(page_title="History Timeline", layout="wide")

df = pd.DataFrame(EVENTS).sort_values("year").reset_index(drop=True)

CATEGORY_COLORS = {
    "Rome": "#c0392b",
    "Istanbul": "#8e44ad",
    "World History": "#2980b9",
}

st.title("Popular Historical Timeline")

with st.sidebar:
    st.header("Filters")
    categories = st.multiselect(
        "Categories",
        options=list(CATEGORY_COLORS.keys()),
        default=list(CATEGORY_COLORS.keys()),
    )

filtered = df[df["category"].isin(categories)]

fig = go.Figure()
for category, group in filtered.groupby("category"):
    fig.add_trace(
        go.Scatter(
            x=group["year"],
            y=group["category"],
            mode="markers+text",
            name=category,
            marker=dict(
                size=30,
                color=CATEGORY_COLORS.get(category, "#7f8c8d"),
                opacity=0.18,
            ),
            text=group["icon"],
            textfont=dict(size=18),
            textposition="middle center",
            customdata=group.index,
            hovertext=group.apply(
                lambda r: f"<b>{r['title']}</b><br>{r['display_date']}", axis=1
            ),
            hoverinfo="text",
        )
    )

fig.update_layout(
    height=420,
    xaxis_title="Year (negative = BCE)",
    yaxis_title="",
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

selected_points = event.selection.points if event and event.selection else []

if selected_points:
    row_index = selected_points[0]["customdata"]
    row = filtered.loc[row_index]
    icon_col, text_col = st.columns([1, 6])
    with icon_col:
        st.markdown(f"<div style='font-size:64px'>{row['icon']}</div>", unsafe_allow_html=True)
    with text_col:
        st.subheader(f"{row['title']} — {row['display_date']}")
        st.caption(row["category"])
        st.write(row["summary"])
else:
    st.info("Click an event on the timeline to see details.")
