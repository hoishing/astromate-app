import streamlit as st
from natal.config import Display
from pathlib import Path

SOURCE_CODE = """\
![github](https://api.iconify.design/bi/github.svg?color=%236FD886&width=20) &nbsp;
[source code](https://github.com/hoishing/astrobro)
"""

ABOUT = f"💫 &nbsp;AstroBro :&nbsp; your pocket astrologer\n\n{SOURCE_CODE}"

PAGE_CONFIG = dict(
    page_title="AstroBro",
    page_icon="💫",
    layout="wide",
    menu_items={
        "About": ABOUT,
        "Get help": "https://github.com/hoishing/astrobro/issues",
    },
)

BODIES = list(Display().keys())
STYLE = f"<style>{Path('style.css').read_text()}</style>"
LOGO = "static/astrobro-logo.png"
CHART_SIZE = 650
SESS = st.session_state

HIST_COL_CONFIG = {
    "chart1": st.column_config.Column(label="main"),
    "city1": st.column_config.Column(label="city"),
    "datetime1": st.column_config.Column(label="datetime"),
    "chart2": st.column_config.Column(label="auxiliary"),
    "city2": st.column_config.Column(label="city"),
    "datetime2": st.column_config.Column(label="datetime"),
}
