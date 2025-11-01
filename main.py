import streamlit as st
from archive import delete_chart
from const import LOGO, PAGE_CONFIG, SESS, STYLE, VAR
from st_screenwidth_detector import screenwidth_detector
from ui import (
    ai_ui,
    chart_ui,
    input_ui,
    segmented_ui,
    sidebar_ui,
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


def input1():
    with st.expander(i("birth_data"), expanded=True):
        input_ui(1)


def input2(title: str):
    with st.container(key=f"input2_{title}"):
        with st.expander(title, expanded=True):
            input_ui(2)


def chart():
    if VAR.name1 and VAR.lat1 and VAR.lon1 and VAR.tz1:
        data1 = natal_data(1)
        if VAR.chart_type == "solar_return_page":
            data1 = data1.solar_return(target_yr=VAR.solar_return_year)
        data2 = natal_data(2) if VAR.name2 and VAR.lat2 and VAR.lon2 and VAR.tz2 else None
        chart_ui(data1, data2)
        utils_ui(2 if data2 else 1, data1, data2)
        if VAR.show_stats:
            stats_ui(data1, data2)
        if VAR.ai_chat and VAR.chart_type == "birth_page":
            ai_ui(data1, data2)


def birth_page():
    input1()
    chart()


def synastry_page():
    input1()
    input2(i("synastry_page"))
    chart()


def transit_page():
    input1()
    input2(i("transit_page"))
    chart()


def solar_return_page():
    input1()
    input2("solar_return_page")
    chart()


sidebar_ui()
segmented_ui()


match SESS.chart_type:
    case "birth_page":
        birth_page()
    case "synastry_page":
        synastry_page()
    case "transit_page":
        transit_page()
    case "solar_return_page":
        solar_return_page()
