import streamlit as st
from datetime import date as Date
from datetime import datetime
from natal.config import Display, DotDict, Orb
from pathlib import Path

SESS = st.session_state
SESS.setdefault("var", DotDict())
VAR = st.session_state.var

ORBS = Orb().model_dump()

DEFAULT_GENERAL_OPTS = {
    "house_sys": "Placidus",
    "lang_num": int(st.query_params.get("lang", 1)),
    "pdf_color": "light",
    "show_stats": True,
    "ai_chat": True,
}

for key in DEFAULT_GENERAL_OPTS:
    VAR.setdefault(key, DEFAULT_GENERAL_OPTS[key])

for aspect in ORBS:
    VAR.setdefault(aspect, ORBS[aspect])

VAR.setdefault("name1", "")
VAR.setdefault("name2", "")
VAR.setdefault("city1", "")
VAR.setdefault("city2", "")
VAR.setdefault("lat1", None)
VAR.setdefault("lon1", None)
VAR.setdefault("tz1", "")
VAR.setdefault("lat2", None)
VAR.setdefault("lon2", None)
VAR.setdefault("tz2", "")
VAR.setdefault("date1", Date(2000, 1, 1))
VAR.setdefault("date2", datetime.now().date())
VAR.setdefault("hr1", 13)
VAR.setdefault("hr2", datetime.now().hour)
VAR.setdefault("min1", 0)
VAR.setdefault("min2", datetime.now().minute)
VAR.setdefault("stepper_unit", "day")

# Non UI variables, no need to handle SESS None bug
VAR.setdefault("chat", None)

for body, val in Display().items():
    for num in "12":
        VAR.setdefault(f"{body}{num}", val)


PAGE_CONFIG = dict(
    page_title="AstroBro",
    page_icon="💫",
    layout="wide",
)

HOUSE_SYS = ["Placidus", "Koch", "Equal", "Whole Sign", "Porphyry", "Campanus", "Regiomontanus"]
STYLE = f"<style>{Path('style.css').read_text()}</style>"
LOGO = "static/astrobro-logo.png"
CHART_SIZE = 650
ROW_HEIGHT = 35
PDF_COLOR = dict(light=":material/palette:", mono=":material/contrast:")

LANGS = ["English", "中文"]
MODELS = [
    "deepseek/deepseek-chat-v3.1:free",
    "google/gemini-2.0-flash-exp:free",
    # "gemini-2.0-flash-lite",
    # "gemini-2.5-flash-lite",
    # "gemini-2.5-flash",
]
I18N = {
    # pages
    "natal_page": ("Natal Chart", "命盤"),
    "synastry_page": ("Synastry Chart", "合盤"),
    "transit_page": ("Transit Chart", "行運"),
    "solar_return_page": ("Solar Return", "太陽回歸"),
    # auth
    "login": ("Login", "登入"),
    "logout": ("Logout", "登出"),
    # general options
    "options": ("Options", "選項"),
    "general": ("General", "一般"),
    "house-system": ("House System", "宮位系統"),
    "pdf-color": ("PDF Color", "PDF 顏色"),
    "language": ("Language", "語言"),
    "statistics": ("Statistics", "統計"),
    # utils ui
    "gen-pdf": ("Generate PDF", "生成 PDF"),
    "download-pdf": ("Download PDF", "下載 PDF"),
    "save-chart": ("Save Chart", "保存星盤"),
    "prev": ("Prev ", "上一"),
    "next": ("Next ", "下一"),
    # "ai_chat": ("AI Chat", "AI 聊天"),
    # orbs
    "orbs": ("Orbs", "容許度"),
    "orb": ("Orb", "容許度"),
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
    "city-placeholder": ("city", "城市"),
    "city-help": ("select or type in the city name", "選擇或輸入城市名稱"),
    "year": ("yr", "年"),
    "month": ("mo", "月"),
    "week": ("wk", "週"),
    "day": ("day", "日"),
    "hour": ("hr", "時"),
    "minute": ("min", "分"),
    "date": ("Date", "日期"),
    "daylight-saving-time": ("Daylight Saving Time(if applicable)", "夏令時間(如適用)"),
    "adjustment": ("Adjustment", "調整"),
    # saved charts
    "saved-charts": ("Saved Charts", "星盤存檔"),
    "no-saved-charts": ("No saved charts", "沒有星盤存檔"),
    "chart-created": ("Chart Created", "星盤已保存"),
    "chart-updated": ("Chart Updated", "星盤已更新"),
    # house sys
    "Placidus": ("Placidus", "普拉西度"),
    "Koch": ("Koch", "科赫"),
    "Equal": ("Equal", "等宫制"),
    "Whole Sign": ("Whole Sign", "整宫制"),
    "Porphyry": ("Porphyry", "波菲利"),
    "Campanus": ("Campanus", "坎帕努斯"),
    "Regiomontanus": ("Regiomontanus", "雷格蒙塔努斯"),
    "latitude-error": (": latitude must be between -66.5 and 66.5", ": 緯度必須在 -66.5 和 66.5 之間"),
    # ai chat
    "thinking": ("thinking", "思考中"),
    "chat-placeholder": ("chat about the astrological chart...", "聊聊這個星盤吧～"),
    "question-1": (
        "What does my birth chart reveal about my personality, strengths, and challenges?",
        "我的出生圖對我的個性、優勢和挑戰有何啟示？",
    ),
    "question-2": (
        "What are my key relationships and how can I improve them?",
        "我的關鍵關係是什麼，如何改善？",
    ),
    "question-3": (
        "What are my career opportunities and how can I make the most of them?",
        "我的職業機會是什麼，如何最大化利用？",
    ),
    "question-4": (
        "Any suggestions on my love life and relationships?",
        "在愛情和人際關係方面有什麼建議？",
    ),
    "question-5": (
        "What are my spiritual and emotional needs, and how can I fulfill them?",
        "我的精神需求和情感需求是什麼，如何滿足？",
    ),
    "question-6": (
        "What are my financial goals and how can I achieve them?",
        "我的財務目標是什麼，如何實現？",
    ),
    "question-7": (
        "What is my career path or life direction? Which way should I be heading?",
        "我的職業生涯或人生方向是什麼？我該朝哪個方向努力？",
    ),
    # stats
    "basic-info": ("Basic Info", "基本資料"),
    "element-vs-modality": ("Element vs Modality", "四元素與三態"),
    "quad-vs-hemi": ("Quadrants vs Hemisphere", "象限與半球"),
    "aspects": ("Aspects", "相位"),
    "aspect": ("Aspect", "相位"),
    # basic info
    "coordinates": ("Coordinates", "座標"),
    "local-time": ("Local Time", "當地時間"),
    # celestial bodies
    "celestial_body": ("Celestial Bodies", "星體"),
    "body": ("Body", "星體"),
    "dignity": ("Dignity", "尊貴"),
    "domicile": ("Domicile", "廟"),
    "exaltation": ("Exaltation", "旺"),
    "detriment": ("Detriment", "陷"),
    "fall": ("Fall", "弱"),
    # signs and houses
    "signs": ("Signs", "星座"),
    "sign": ("Sign", "星座"),
    "houses": ("Houses", "宮位"),
    "house": ("House", "宮位"),
    "bodies": ("Bodies", "星體"),
    "cusp": ("Cusp", "宮頭"),
    # cross ref
    "rows": ("rows", "列"),
    "cols": ("cols", "行"),
    # pdf
}
