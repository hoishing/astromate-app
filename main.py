import streamlit as st
from archive import delete_chart
from const import SESS, set_default_values
from pathlib import Path
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


st.set_page_config(
    page_title="AstroBro",
    page_icon="💫",
    layout="wide",
    initial_sidebar_state="auto",
)
st.logo("static/astrobro-logo.png")
st.html(f"<style>{Path('style.css').read_text()}</style>")


def input(id: int, title: str):
    with st.expander(title, expanded=True):
        input_ui(id)


def chart():
    if SESS.name1 and SESS.lat1 and SESS.lon1 and SESS.tz1:
        data1 = natal_data(1)
        if SESS.chart_type == "solar_return_page":
            data1 = data1.solar_return(target_yr=SESS.solar_return_year)
        data2 = natal_data(2) if SESS.name2 and SESS.lat2 and SESS.lon2 and SESS.tz2 else None
        chart_ui(data1, data2)
        utils_ui(2 if data2 else 1, data1, data2)
        if SESS.show_stats:
            stats_ui(data1, data2)
        if SESS.ai_chat and SESS.chart_type == "birth_page":
            ai_ui(data1, data2)


def birth_page():
    input(1, i("birth_data"))
    chart()


def synastry_page():
    input(1, i("birth_data"))
    input(2, i("synastry_page"))
    chart()


def transit_page():
    input(1, i("birth_data"))
    input(2, i("transit_page"))
    chart()


def solar_return_page():
    input(1, i("birth_data"))
    chart()


set_default_values()
if SESS.chart_type is None:
    SESS.chart_type = SESS.selected_chart_type
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
