import streamlit as st
from archive import delete_chart
from const import LOGO, PAGE_CONFIG, SESS, STYLE
from st_screenwidth_detector import screenwidth_detector
from ui import (
    ai_ui,
    chart_ui,
    display_opt,
    general_opt,
    input_ui,
    orb_opt,
    saved_charts_ui,
    stats_ui,
    utils_ui,
)
from utils import i, natal_data

# Handle delete requests
delete_hash = st.query_params.get("delete")
if delete_hash and st.user.is_logged_in:
    delete_chart(delete_hash)
    st.query_params.clear()


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

    if st.user.is_logged_in:
        saved_charts_ui()
        st.button(i("logout"), icon=":material/logout:", width="stretch", on_click=st.logout)
    else:
        st.button(i("login"), icon=":material/login:", width="stretch", on_click=st.login)

with st.expander(i("birth-chart"), expanded=True):
    input_ui(1)

with st.expander(i("synastry-chart")):
    input_ui(2)

SESS.chart_size = min(screenwidth_detector() + 18, 650)

if SESS.name1 and SESS.lat1 and SESS.lon1 and SESS.tz1:
    data1 = natal_data(1)
    data2 = natal_data(2) if SESS.name2 and SESS.lat2 and SESS.lon2 and SESS.tz2 else None
    chart_ui(data1, data2)
    utils_ui(2 if data2 else 1)
    if SESS.show_stats:
        stats_ui(data1, data2)
    if SESS.ai_chat:
        ai_ui(data1, data2)
