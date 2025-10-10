import streamlit as st
from natal.config import Display, Orb
from pathlib import Path

SESS = st.session_state

PAGE_CONFIG = dict(
    page_title="AstroBro",
    page_icon="💫",
    layout="wide",
)

HOUSE_SYS = ["Placidus", "Koch", "Equal", "Whole Sign", "Porphyry", "Campanus", "Regiomontanus"]
ORBS = Orb().model_dump()
BODIES = list(Display.model_fields)
STYLE = f"<style>{Path('style.css').read_text()}</style>"
LOGO = "static/astrobro-logo.png"
CHART_SIZE = 650
ROW_HEIGHT = 35
PRINT_COLOR = dict(light=":material/palette:", mono=":material/contrast:")

LANGS = ["English", "中文"]
MODELS = [
    "deepseek/deepseek-chat-v3.1:free",
    "google/gemini-2.0-flash-exp:free",
    # "gemini-2.0-flash-lite",
    # "gemini-2.5-flash-lite",
    # "gemini-2.5-flash",
]
I18N = {
    # auth
    "login": ("Login", "登入"),
    "logout": ("Logout", "登出"),
    # general options
    "options": ("Options", "選項"),
    "general": ("General", "一般"),
    "house-system": ("House System", "宮位系統"),
    "print-color": ("Print Color", "列印顏色"),
    "language": ("Language", "語言"),
    "statistics": ("Statistics", "統計"),
    # "ai_chat": ("AI Chat", "AI 聊天"),
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
    # elements
    "fire": ("Fire", "火象"),
    "air": ("Air", "風象"),
    "water": ("Water", "水象"),
    "earth": ("Earth", "土象"),
    "sum": ("Sum", "總和"),
    # modality
    "cardinal": ("Cardinal", "開創"),
    "fixed": ("Fixed", "固定"),
    "mutable": ("Mutable", "變動"),
    # polarity
    "polarity": ("Polarity", "陰陽"),
    "pos": ("Positive", "陽"),
    "neg": ("Negative", "陰"),
    # hemisphere
    "eastern": ("Eastern", "東半球"),
    "western": ("Western", "西半球"),
    "northern": ("Northern", "北半球"),
    "southern": ("Southern", "南半球"),
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
    "asc_node": ("North Node", "北交"),
    "asc": ("ASC", "上升"),
    "ic": ("IC", "天底"),
    "dsc": ("DSC", "下降"),
    "mc": ("MC", "天頂"),
    "chiron": ("Chiron", "凱龍"),
    "ceres": ("Ceres", "穀神"),
    "pallas": ("Pallas", "智神"),
    "juno": ("Juno", "婚神"),
    "vesta": ("Vesta", "灶神"),
    "inner-planets": ("Inner", "內行星"),
    "classic": ("Classic", "經典"),
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
    "no-saved-charts": ("No saved charts", "沒有星盤存檔"),
    # house sys
    "Placidus": ("Placidus", "普拉西度"),
    "Koch": ("Koch", "科赫"),
    "Equal": ("Equal", "等宫制"),
    "Whole Sign": ("Whole Sign", "整宫制"),
    "Porphyry": ("Porphyry", "波菲利"),
    "Campanus": ("Campanus", "坎帕努斯"),
    "Regiomontanus": ("Regiomontanus", "雷格蒙塔努斯"),
    # ai chat
    "thinking": ("thinking", "思考中"),
    "chat-placeholder": ("chat about the astrological chart...", "聊聊這個星盤吧～"),
    # stats
    "basic-info": ("Basic Info", "基本資訊"),
    "element-vs-modality": ("Element vs Modality", "四元素與三態"),
    "quad-vs-hemi": ("Quadrants vs Hemisphere", "象限與半球"),
    "aspects": ("Aspects", "相位"),
    # basic info
    "coordinates": ("Coordinates", "座標"),
    "local-time": ("Local Time", "當地時間"),
    # celestial bodies
    "celestial_body": ("Celestial Bodies", "星體"),
    "body": ("Body", "星體"),
    "sign": ("Sign", "星座"),
    "house": ("House", "宮位"),
    "dignity": ("Dignity", "廟旺陷弱"),
    "domicile": ("Domicile", "廟"),
    "exaltation": ("Exaltation", "旺"),
    "detriment": ("Detriment", "陷"),
    "fall": ("Fall", "弱"),
    # signs and houses
    "body-in-signs": ("Celestial Bodies in Signs", "星體星座分布"),
    "body-in-houses": ("Celestial Bodies in Houses", "星體宮位分布"),
    "bodies": ("Bodies", "星體"),
    "cusp": ("Cusp", "宮頭"),
    # cross ref
    "rows": ("rows", "列"),
    "cols": ("cols", "行"),
}
