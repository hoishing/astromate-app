import sqlite3
import streamlit as st
from const import I18N, MODELS, SESS
from datetime import datetime, timedelta
from functools import reduce
from natal import Config, Data, Stats
from natal.const import ASPECT_NAMES
from openai import OpenAI
from textwrap import dedent
from typing import Literal, TypedDict
from zoneinfo import ZoneInfo


def i(key: str) -> str:
    return I18N[key][SESS.get("lang_num", 0)]


def utc_of(id: int) -> datetime:
    """convert local datetime to utc datetime"""
    naive_dt = get_dt(id)
    tzinfo = ZoneInfo(SESS[f"tz{id}"])
    dt = naive_dt.replace(tzinfo=tzinfo)
    return dt.astimezone(ZoneInfo("UTC"))


def get_dt(id: int) -> datetime:
    """get datetime from session state"""
    date = SESS[f"date{id}"]
    hr = SESS[f"hr{id}"]
    minute = SESS[f"min{id}"]
    return datetime(date.year, date.month, date.day, hr, minute)


@st.cache_resource
def db_conn() -> sqlite3.Connection:
    return sqlite3.connect("astrobro.db", check_same_thread=False)


@st.cache_data
def all_timezones() -> list[str]:
    """get all timezones from database"""
    cursor = db_conn().cursor()
    cursor.execute("SELECT timezone FROM timezone")
    return [x[0] for x in cursor.fetchall()]


@st.cache_data
def all_cities() -> list[tuple[str, str]]:
    """get all cities name and country from database"""
    cursor = db_conn().cursor()
    cursor.execute("SELECT name, country FROM cities")
    return cursor.fetchall()


def set_lat_lon_dt_tz(id: int) -> dict:
    """return lat, lon, utc datetime from a chart input ui"""
    if not (city_tuple := SESS[f"city{id}"]):
        return
    columns = "lat, lon, timezone"
    cursor = db_conn().cursor()
    cursor.execute(f"SELECT {columns} FROM cities WHERE name = ? and country = ?", city_tuple)
    (lat, lon, timezone) = cursor.fetchone()
    SESS[f"lat{id}"] = lat
    SESS[f"lon{id}"] = lon
    SESS[f"tz{id}"] = timezone


def natal_data(id: int) -> Data:
    """return natal data from a chart input ui"""
    display = SESS[f"display{id}"]
    aspects = {aspect: SESS[aspect] for aspect in ASPECT_NAMES}
    return Data(
        name=SESS[f"name{id}"],
        lat=SESS[f"lat{id}"],
        lon=SESS[f"lon{id}"],
        utc_dt=utc_of(id),
        config=Config(
            house_sys=SESS.house_sys[0],
            theme_type=SESS.theme_type,
            orb=aspects,
            display=display,
        ),
    )


def step(chart_id: int, unit: str, delta: Literal[1, -1]):
    """step implementation for stepper ui"""
    dt = get_dt(chart_id)

    match unit:
        case "week":
            delta = timedelta(weeks=delta)
        case "day":
            delta = timedelta(days=delta)
        case "hour":
            delta = timedelta(hours=delta)
        case "minute":
            delta = timedelta(minutes=delta)
        case "month":
            new_month = dt.month + delta
            new_year = dt.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            dt = dt.replace(year=new_year, month=new_month)
        case "year":
            dt = dt.replace(year=dt.year + delta)

    if unit not in ["month", "year"]:
        dt += delta

    SESS[f"date{chart_id}"] = dt.date()
    SESS[f"hr{chart_id}"] = dt.hour
    SESS[f"min{chart_id}"] = dt.minute


class Message(TypedDict):
    role: Literal["developer", "user", "assistant"]
    content: str


class OpenRouterChat:
    def __init__(self, client: OpenAI, model: str, system_message: str):
        self.client = client
        self.model = model
        self.messages = [Message(role="developer", content=system_message)]

    def send_message_stream(self, prompt: str):
        """Send message and return streaming response"""
        self.messages.append(Message(role="user", content=prompt))

        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages, stream=True
        )

        full_response = ""
        for chunk in response:
            if content := chunk.choices[0].delta.content:
                full_response += content
                yield content

        # Add assistant response to history
        self.messages.append(Message(role="assistant", content=full_response))


def new_chat(data1: Data, data2: Data = None) -> OpenRouterChat:
    stats = Stats(data1=data1, data2=data2)
    chart_data = reduce(
        lambda x, y: x + y,
        (
            stats.ai_md(tb, 2 if tb == "house" else 3)
            for tb in ["celestial_body", "house", "aspect", "quadrant", "hemisphere"]
        ),
    )
    lang = "Traditional Chinese" if SESS.lang_num else "English"
    sys_prompt = dedent(f"""\
            You are an expert astrologer. You answer questions about this astrological chart:
            
            <chart>
            {chart_data}
            </chart>

            # Instructions
            - Answer the user's questions based on the chart data.
            - Use {lang} to reply.
            """)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"]
    )
    model = MODELS[0]  # Use x-ai/grok-4-fast:free instead of Gemini
    return OpenRouterChat(client, model, sys_prompt)


def scroll_to_bottom():
    import random
    import string

    # random chars to avoid cache, make sure execute after rerun
    random_chars = random.choices(string.ascii_lowercase, k=10)
    js = f"""
    <script>
    function scrollToBottom(dummy_var) {{
        const target = parent.document.querySelector(".stMainBlockContainer");
        target.scrollTo({{
            top: target.scrollHeight,
            behavior: "smooth",
        }});
        console.log(target.scrollHeight);
    }}
    scrollToBottom({random_chars});
    </script>
    """
    st.components.v1.html(js, height=0, width=0)
