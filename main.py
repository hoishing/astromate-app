import streamlit as st
from archive import delete_chart
from const import LOGO, PAGE_CONFIG, STYLE, VAR
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
    delete_chart(st.user.email, delete_hash)
    st.query_params.clear()


st.set_page_config(**PAGE_CONFIG)
st.logo(LOGO)
st.html(STYLE)

VAR.chart_size = min(screenwidth_detector() + 16, 650)


def sidebar():
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


def input1():
    with st.expander(i("birth-chart"), expanded=True):
        input_ui(1)


def input2():
    with st.expander(i("synastry-chart")):
        input_ui(2)


def chart():
    if VAR.name1 and VAR.lat1 and VAR.lon1 and VAR.tz1:
        data1 = natal_data(1)
        data2 = natal_data(2) if VAR.name2 and VAR.lat2 and VAR.lon2 and VAR.tz2 else None
        chart_ui(data1, data2)
        utils_ui(2 if data2 else 1, data1, data2)
        if VAR.show_stats:
            stats_ui(data1, data2)
        if VAR.ai_chat:
            ai_ui(data1, data2)


def natal_page():
    sidebar()
    input1()
    chart()


def synastry_page():
    sidebar()
    input1()
    input2()
    chart()


def transit_page():
    sidebar()
    input1()
    input2()
    chart()


def solar_return_page():
    sidebar()
    input1()
    chart()


pages = []

icons = {
    "natal": "person",
    "synastry": "group",
    "transit": "calendar_today",
    "solar_return": "sunny",
}

for func in [natal_page, synastry_page, transit_page, solar_return_page]:
    page_name = func.__name__.removesuffix("_page")
    pages.append(
        st.Page(
            page=func,
            title=i(func.__name__),
            icon=f":material/{icons[page_name]}:",
            url_path=page_name,
        )
    )

pg = st.navigation(pages=pages)
pg.run()
