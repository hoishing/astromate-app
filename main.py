import streamlit as st
from archive import delete_chart
from const import SESS, set_default_values
from ui import (
    ai_ui,
    chart_ui,
    input_ui,
    segmented_ui,
    sidebar_ui,
    stats_ui,
    utils_ui,
)
from utils import i, is_form_valid, natal_data

# Handle delete requests
delete_hash = st.query_params.get("delete")
if delete_hash and st.user.is_logged_in:
    delete_chart(st.user.email, delete_hash)
    st.query_params.clear()


st.set_page_config(
    page_title="AstroMate",
    page_icon="static/favicon-256.png",
    layout="wide",
    initial_sidebar_state="auto",
)
st.logo("static/astromate-logo.png")
st.html("style.css")


def input(title1: str, icon2: str | None = None, title2: str | None = None):
    with st.expander(title1, expanded=True):
        input_ui(1)
        if icon2 and title2:
            with st.container(key="input_container"):
                st.write("")
                st.markdown(f"###### :material/{icon2}: {title2}")
                input_ui(2)


set_default_values()
sidebar_ui()
segmented_ui()

# input data for different chart types
match SESS.chart_type:
    case "birth_page":
        input(i("birth_data"))
    case "synastry_page":
        input(i("birth_data"), "group", i("synastry_data"))
    case "transit_page":
        input(i("birth_data"), "calendar_clock", i("transit_data"))
    case "solar_return_page":
        input(i("birth_data"))

data1 = natal_data(1) if is_form_valid(1) else None
if not data1:
    st.stop()

data2 = natal_data(2) if is_form_valid(2) else None
if SESS.chart_type in ["synastry_page", "transit_page"] and not data2:
    st.stop()

chart_ui(data1, data2)
utils_ui(data1, data2)
stats_ui(data1, data2)
ai_ui(data1, data2)
