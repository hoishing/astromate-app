import pandas as pd
import streamlit as st
from const import HIST_COLUMN_CONFIG, HIST_USE_COLS, LOGO, PAGE_CONFIG, STYLE
from st_screenwidth_detector import screenwidth_detector
from ui import (
    chart_ui,
    data_obj,
    display_opt,
    general_opt,
    input_ui,
    orb_opt,
    stats_ui,
    stepper_ui,
)

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

    st.subheader(":material/save_alt: Saved Charts")
    df = pd.read_csv(
        "mock.csv",
        usecols=HIST_USE_COLS,
    )
    st.dataframe(
        df,
        hide_index=True,
        column_config=HIST_COLUMN_CONFIG,
    )

with st.expander("Main Chart", expanded=True):
    name1, city1 = input_ui(1)

with st.expander("Auxiliary Chart"):
    name2, city2 = input_ui(2)

st.session_state.chart_size = min(screenwidth_detector() + 20, 650)

if name1 and city1:
    data1, data2 = data_obj(name1, city1, name2, city2)
    chart_ui(data1, data2)
    stepper_ui(2 if data2 else 1)
    if st.session_state.show_stats:
        stats_ui(data1, data2)
