import streamlit as st
from enum import StrEnum
from natal import HouseSys, ThemeType
from natal.const import ASPECT_NAMES
from pathlib import Path

SESS = st.session_state

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

BODIES = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "asc_node",
    "asc",
    # "ic",
    "dsc",
    "mc",
]
HOUSE_SYS = HouseSys._member_names_
ASPECTS = ASPECT_NAMES[:5]
STYLE = f"<style>{Path('style.css').read_text()}</style>"
LOGO = "static/astrobro-logo.png"
CHART_SIZE = 650
CHART_COLORS = dict(
    zip(ThemeType.__args__, [f":material/{x}:" for x in ["sunny", "dark_mode", "contrast"]])
)
HIST_COL_CONFIG = {
    "chart1": st.column_config.Column(label="main"),
    "city1": st.column_config.Column(label="city"),
    "datetime1": st.column_config.Column(label="datetime"),
    "chart2": st.column_config.Column(label="auxiliary"),
    "city2": st.column_config.Column(label="city"),
    "datetime2": st.column_config.Column(label="datetime"),
}

LANGS = ["English", "中文"]
I18N = {
    # planets
    "sun": ("Sun", "日"),
    "moon": ("Moon", "月"),
    "mercury": ("Mercury", "水"),
    "venus": ("Venus", "金"),
    "mars": ("Mars", "火"),
    "jupiter": ("Jupiter", "木"),
    "saturn": ("Saturn", "土"),
    "uranus": ("Uranus", "天王"),
    "neptune": ("Neptune", "海王"),
    "pluto": ("Pluto", "冥王"),
    "asc_node": ("North Node", "北交"),
    "asc": ("ASC", "上升"),
    "ic": ("IC", "天底"),
    "dsc": ("DSC", "下降"),
    "mc": ("MC", "天頂"),
    "city-placeholder": ("- custom -", "- 自定 -"),
}
