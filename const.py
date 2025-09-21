import streamlit as st
from natal import ThemeType
from natal.config import Display, Orb
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

HOUSE_SYS = ["Placidus", "Koch", "Equal", "Whole Sign", "Porphyry", "Campanus", "Regiomontanus"]
ORBS = Orb().model_dump()
BODIES = list(Display.model_fields)
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
MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]
I18N = {
    # general options
    "options": ("Options", "選項"),
    "general": ("General", "一般"),
    "house-system": ("House System", "宮位系統"),
    "chart-color": ("Chart Color", "星盤顏色"),
    "language": ("Language", "語言"),
    "statistics": ("Statistics", "統計"),
    # orbs
    "orbs": ("Orbs", "容許度"),
    "conjunction": ("Conjunction", "合相"),
    "square": ("Square", "四分相"),
    "trine": ("Trine", "三分相"),
    "opposition": ("Opposition", "二分相"),
    "sextile": ("Sextile", "六分相"),
    "quincunx": ("Quincunx", "梅花相"),
    "transit": ("Transit", "行運"),
    "default": ("Default", "預設"),
    # planet display
    "birth": ("Birth", "命盤"),
    "synastry": ("Synastry", "合盤"),
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
    "north_node": ("North Node", "北交"),
    "asc": ("ASC", "上升"),
    "ic": ("IC", "天底"),
    "dsc": ("DSC", "下降"),
    "mc": ("MC", "天頂"),
    "inner-planets": ("Inner Planets", "內行星"),
    # input form
    "name": ("Name", "名稱"),
    "city": ("City", "城市"),
    "latitude": ("Latitude", "緯度"),
    "longitude": ("Longitude", "經度"),
    "timezone": ("Timezone", "時區"),
    "birth-chart": ("Birth Chart", "命盤"),
    "synastry-chart": ("Synastry Chart", "合盤"),
    "city-placeholder": ("- custom -", "- 自定 -"),
    "year": ("yr", "年"),
    "month": ("mo", "月"),
    "week": ("wk", "週"),
    "day": ("day", "日"),
    "hour": ("hr", "時"),
    "minute": ("min", "分"),
    "date": ("Date", "日期"),
    "adjustment": ("Adjustment", "調整"),
    # saved charts
    "saved-charts": ("Saved Charts", "星盤存檔"),
    # house sys
    "Placidus": ("Placidus", "普拉西度"),
    "Koch": ("Koch", "科赫"),
    "Equal": ("Equal", "等宫制"),
    "Whole Sign": ("Whole Sign", "整宫制"),
    "Porphyry": ("Porphyry", "波菲利"),
    "Campanus": ("Campanus", "坎帕努斯"),
    "Regiomontanus": ("Regiomontanus", "雷格蒙塔努斯"),
}
