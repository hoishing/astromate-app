import pandas as pd
import streamlit as st
from const import HIST_COL_CONFIG, LOGO, PAGE_CONFIG, SESS, STYLE
from st_screenwidth_detector import screenwidth_detector
from ui import chart_ui, display_opt, general_opt, input_ui, orb_opt, stats_ui, stepper_ui
from utils import natal_data

st.set_page_config(**PAGE_CONFIG)
st.logo(LOGO)
st.html(STYLE)

dt_column = st.column_config.DatetimeColumn()

with st.sidebar:
    with st.expander("Options", expanded=True):
        t1, t2, t3, t4 = st.tabs(["General", "Orbs", "Main", "Auxiliary"])
        with t1:
            general_opt()
        with t2:
            orb_opt()
        with t3:
            display_opt(1)
        with t4:
            display_opt(2)

    # TODO: replace with database
    st.subheader("Saved Charts")
    df = pd.read_csv("mock.csv", usecols=HIST_COL_CONFIG.keys())
    height = (len(df) + 1) * 35
    st.dataframe(df, hide_index=True, column_config=HIST_COL_CONFIG, height=height)

with st.expander("Main Chart", expanded=True):
    name1, city1 = input_ui(1)

with st.expander("Auxiliary Chart"):
    name2, city2 = input_ui(2)

SESS.chart_size = min(screenwidth_detector() + 20, 650)

if name1 and city1:
    data1 = natal_data(1)
    data2 = natal_data(2) if name2 and city2 else None
    chart_ui(data1, data2)
    stepper_ui(2 if data2 else 1)
    if SESS.show_stats:
        stats_ui(data1, data2)
