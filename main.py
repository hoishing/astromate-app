import pandas as pd
import streamlit as st
from const import HIST_COL_CONFIG, LOGO, PAGE_CONFIG, ROW_HEIGHT, SESS, STYLE
from st_screenwidth_detector import screenwidth_detector
from ui import ai_ui, chart_ui, display_opt, general_opt, input_ui, orb_opt, stats_ui, stepper_ui
from utils import i, natal_data

st.set_page_config(**PAGE_CONFIG)
st.logo(LOGO)
st.html(STYLE)

dt_column = st.column_config.DatetimeColumn()

with st.sidebar:
    with st.expander(i("options"), expanded=True):
        labels = ["general", "orbs", "birth", "synastry"]
        t1, t2, t3, t4 = st.tabs([i(label) for label in labels])
        with t1:
            general_opt()
        with t2:
            orb_opt()
        with t3:
            display_opt(1)
        with t4:
            display_opt(2)

    # TODO: replace with database
    st.subheader(i("saved-charts"))
    df = pd.read_csv("mock.csv", usecols=HIST_COL_CONFIG.keys())
    df1 = df.iloc[:0]
    height = (len(df1) + 1) * ROW_HEIGHT + 2
    st.dataframe(
        df1, hide_index=True, column_config=HIST_COL_CONFIG, height=height, row_height=ROW_HEIGHT
    )

with st.expander(i("birth-chart"), expanded=True):
    input_ui(1)

with st.expander(i("synastry-chart")):
    input_ui(2)

SESS.chart_size = min(screenwidth_detector() + 18, 650)

if SESS.name1 and SESS.lat1 and SESS.lon1 and SESS.tz1:
    data1 = natal_data(1)
    data2 = natal_data(2) if SESS.name2 and SESS.lat2 and SESS.lon2 and SESS.tz2 else None
    chart_ui(data1, data2)
    stepper_ui(2 if data2 else 1)
    if SESS.show_stats:
        stats_ui(data1, data2)
    if SESS.ai_chat:
        ai_ui(data1, data2)
