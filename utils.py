import json
import logging
import pandas as pd
import sqlite3
import streamlit as st
from const import I18N, MODELS, SESS
from datetime import datetime, timedelta
from functools import reduce
from io import BytesIO
from natal import Chart, Config, Data, Stats
from natal.config import LightTheme
from natal.const import ASPECT_NAMES
from openai import OpenAI
from pathlib import Path
from tagit import div, main, style, table, td, tr
from textwrap import dedent
from typing import Iterable, Literal, TypedDict
from weasyprint import HTML
from zoneinfo import ZoneInfo

# suppress fontTools warnings
logging.getLogger("fontTools").setLevel(logging.ERROR)


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
def cities_db() -> sqlite3.Connection:
    return sqlite3.connect("cities.db", check_same_thread=False)


@st.cache_resource
def data_db() -> sqlite3.Connection:
    return sqlite3.connect("data.db", check_same_thread=False)


@st.cache_data
def all_timezones() -> list[str]:
    """get all timezones from database"""
    cursor = cities_db().cursor()
    cursor.execute("SELECT timezone FROM timezone")
    return [x[0] for x in cursor.fetchall()]


@st.cache_data
def all_cities() -> list[tuple[str, str]]:
    """get all cities name and country from database"""
    cursor = cities_db().cursor()
    cursor.execute("SELECT name, country FROM cities")
    return cursor.fetchall()


def set_lat_lon_dt_tz(id: int, city_tuple: tuple[str, str]) -> dict:
    """return lat, lon, utc datetime from a chart input ui"""
    # print(type(city_tuple), city_tuple)
    columns = "lat, lon, timezone"
    cursor = cities_db().cursor()
    cursor.execute(f"SELECT {columns} FROM cities WHERE name = ? and country = ?", city_tuple)
    lat, lon, timezone = cursor.fetchone()
    SESS[f"lat{id}"] = lat
    SESS[f"lon{id}"] = lon
    SESS[f"tz{id}"] = timezone


def natal_data(id: int) -> Data:
    """return natal data from a chart input ui"""
    display = SESS[f"display{id}"]
    aspects = {aspect: SESS[aspect] for aspect in ASPECT_NAMES}
    hse_1st_char = SESS.house_sys[0]
    return Data(
        name=SESS[f"name{id}"],
        lat=SESS[f"lat{id}"],
        lon=SESS[f"lon{id}"],
        utc_dt=utc_of(id),
        config=Config(house_sys=hse_1st_char, orb=aspects, display=display),
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
    stats = Stats(
        data1=data1, data2=data2, city1=SESS.city1, city2=SESS.city2, tz1=SESS.tz1, tz2=SESS.tz2
    )
    chart_data = reduce(
        lambda x, y: x + y,
        (stats.ai_md(tb) for tb in ["celestial_body", "house", "aspect", "quadrant", "hemisphere"]),
    )
    lang = "Traditional Chinese" if SESS.lang_num else "English"
    sys_prompt = dedent(f"""\
            You are an expert astrologer. You answer questions about this astrological chart data:
            
            <chart_data>
            {chart_data}
            </chart_data>

            # Chart Data Tables Description
            - Celestial Bodies: sign, house and dignity of specific celestial body
            - Signs: distribution of celestial bodies in the 12 signs
            - Houses: distribution of celestial bodies in the 12 houses
            - Elements: distribution of celestial bodies in the 4 elements
            - Modality: distribution of celestial bodies in the 3 modalities
            - Polarity: distribution of celestial bodies in the 2 polarities
            - Aspects: aspects between celestial bodies
            - Quadrants: distribution of celestial bodies in the 4 quadrants
            - Hemispheres: distribution of celestial bodies in the 4 hemispheres

            # Instructions
            - Answer the user's questions based on the chart data.
            - think about the followings when answering the user's questions:
              - do celestial bodies concentrate in certain signs, houses, elements, modality, polarity, quadrant, or hemisphere?
              - do aspects between celestial bodies form certain patterns?
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


def all_charts() -> pd.DataFrame | None:
    sql = "select data, hash from charts where email = ? order by updated_at desc"
    cursor = data_db().cursor()
    cursor.execute(sql, (st.user.email,))
    all_data = cursor.fetchall()
    if not all_data:
        return None
    df = pd.DataFrame([{**json.loads(d), "hash": h} for (d, h) in all_data])
    df.set_index("hash", inplace=True, drop=False)
    df.hash = "?delete=" + df.hash
    return df


# stats and pdf report =========================================================


def html_table(grid: list[Iterable]) -> str:
    """converts list of iterable into an HTML table"""
    rows = []
    for row in grid:
        cells = []
        for cell in row:
            if isinstance(cell, str) and cell.startswith("null:"):
                cells.append(td(cell.split(":")[1], colspan=2))
            else:
                cells.append(td(cell))
        rows.append(tr(cells))
    return table(rows)


def html_section(title: str, grid: list[Iterable], class_: str = "") -> str:
    """creates an HTML section with a title and data table"""
    return div(
        div(title, class_="title") + html_table(grid),
        class_="section " + class_,
    )


def pdf_io(html: str) -> BytesIO:
    """PDF generation from HTML string"""
    fp = BytesIO()
    HTML(string=html).write_pdf(fp)
    return fp


def stats_html(data1: Data, data2: Data = None):
    stats = Stats(
        data1=data1, data2=data2, city1=SESS.city1, city2=SESS.city2, tz1=SESS.tz1, tz2=SESS.tz2
    )
    basic_info_headers = [i("name"), i("city"), i("coordinates"), i("local-time")]
    basic_info = html_section(i("basic-info"), stats.basic_info(basic_info_headers))

    ele_mod_headers = [i("fire"), i("air"), i("water"), i("earth"), i("sum")]
    ele_mod_row = [i("cardinal"), i("fixed"), i("mutable"), i("sum")]
    ele_mod_polor = [i("polarity"), i("pos"), i("neg")]
    ele_mod_grid = stats.element_vs_modality(ele_mod_headers, ele_mod_row, ele_mod_polor)
    ele_mod = html_section(i("element-vs-modality"), ele_mod_grid)

    quad_hemi_headers = [i("eastern"), i("western"), i("northern"), i("southern"), i("sum")]
    quad_hemi_grid = stats.quadrants_vs_hemisphere(quad_hemi_headers)
    quad_hemi = html_section(i("quad-vs-hemi"), quad_hemi_grid)

    body_headers = [i("body"), i("sign"), i("house"), i("dignity")]
    dignity_labels = [i("domicile"), i("exaltation"), i("fall"), i("detriment")]
    bodies_grid = stats.celestial_body(1, body_headers, dignity_labels)
    user_name = f" - {data1.name}" if data2 else ""
    bodies = html_section(i("celestial_body") + user_name, bodies_grid)
    houses_title = f"{i('houses')} - {i(SESS.house_sys)}"

    if data2:
        # bodies 2
        bodies_grid2 = stats.celestial_body(2, body_headers, dignity_labels)
        bodies2 = html_section(i("celestial_body") + f" - {data2.name}", bodies_grid2)
        bodies += bodies2
        # sign distribution 1 & 2
        synastry_sign_headers = [i("sign"), data1.name, data2.name, i("sum")]
        synastry_signs_grid = stats.signs(headers=synastry_sign_headers)
        signs = html_section(i("signs"), synastry_signs_grid)
        # house distribution
        synastry_houses_headers = [i("house"), i("cusp"), data1.name, data2.name, i("sum")]
        synastry_houses_grid = stats.houses(headers=synastry_houses_headers)
        houses = html_section(houses_title, synastry_houses_grid)
        # cross ref
        aspects_title = f"{i('aspects')} - {data1.name}: {i('rows')} / {data2.name}: {i('cols')}"
    else:
        # sign distribution 1
        sign_headers = [i("sign"), i("bodies"), i("sum")]
        signs_grid = stats.signs(headers=sign_headers)
        signs = html_section(i("signs"), signs_grid)
        # house distribution 1
        houses_headers = [i("house"), i("cusp"), i("bodies"), i("sum")]
        houses_grid = stats.houses(headers=houses_headers)
        houses = html_section(houses_title, houses_grid)
        aspects_title = i("aspects")

    aspect_grid = stats.aspect_grid(total_label=i("sum"))
    aspect_cls = "" if data2 else "aspect_grid"
    aspects = html_section(aspects_title, aspect_grid, class_=aspect_cls)

    html = basic_info + ele_mod + quad_hemi + bodies + signs + houses + aspects
    return html


def pdf_html(data1: Data, data2: Data = None):
    """html source for PDF report"""
    data1.config.theme_type = SESS.pdf_color
    data1.config.chart.stroke_width = 0.7

    stats = Stats(
        data1=data1, data2=data2, city1=SESS.city1, city2=SESS.city2, tz1=SESS.tz1, tz2=SESS.tz2
    )
    chart = Chart(data1, width=400, data2=data2)

    basic_info_title = i("basic-info")
    basic_info_headers = [i("name"), i("city"), i("coordinates"), i("local-time")]
    ele_vs_mod_title = i("element-vs-modality")
    ele_vs_mod_headers = ["🜂", "🜁", "🜄", "🜃", "∑"]
    ele_vs_mod_row_label = ["⟑", "⊟", "𛰣", "∑"]
    ele_vs_mod_polarity_label = ["◐", "+", "-"]
    quad_vs_hemi_title = i("quad-vs-hemi")
    quad_vs_hemi_headers = [i("eastern"), i("western"), i("northern"), i("southern"), "∑"]
    body_headers = [i("body"), i("sign"), i("house"), i("dignity")]
    dignity_labels = ["⏫", "🔼", "⏬", "🔽"]
    aspects_title = i("aspects")
    signs_title = i("signs")
    signs_headers = [i("sign")]
    houses_title = f"{i('houses')} - {i(SESS.house_sys)}"
    if data2:
        body_title1 = i("celestial_body") + f" - {data1.name}"
        body_title2 = i("celestial_body") + f" - {data2.name}"
        signs_headers = [i("sign"), data1.name, data2.name, "∑"]
        houses_headers = [i("house"), i("cusp"), data1.name, data2.name, "∑"]
    else:
        body_title1 = i("celestial_body")
        signs_headers = [i("sign"), i("bodies"), "∑"]
        houses_headers = [i("house"), i("cusp"), i("bodies"), "∑"]

    orb_title = i("orbs")
    orb_headers = [i("aspect"), i("orb")]

    row1 = div(
        html_section(basic_info_title, stats.basic_info(basic_info_headers))
        + html_section(
            ele_vs_mod_title,
            stats.element_vs_modality(
                headers=ele_vs_mod_headers,
                row_label=ele_vs_mod_row_label,
                polarity_label=ele_vs_mod_polarity_label,
                pdf=True,
            ),
        )
        + html_section(
            quad_vs_hemi_title,
            stats.quadrants_vs_hemisphere(headers=quad_vs_hemi_headers, pdf=True),
        ),
        class_="info_col",
    ) + div(chart.svg, class_="chart")

    body_params = {"headers": body_headers, "dignity_labels": dignity_labels, "pdf": True}
    row2 = html_section(body_title1, stats.celestial_body(1, **body_params))

    if stats.data2:
        row2 += html_section(body_title2, stats.celestial_body(2, **body_params))

    row2 += html_section(
        aspects_title,
        grid=stats.aspect_grid(total_label="∑", pdf=True),
        class_="" if data2 else "aspect_grid",
    )
    row3 = (
        html_section(signs_title, stats.signs(headers=signs_headers, pdf=True))
        + html_section(houses_title, stats.houses(headers=houses_headers, pdf=True))
        + html_section(orb_title, stats.orb_settings(headers=orb_headers))
    )
    css = Path(__file__).parent.joinpath("pdf.css").read_text()
    rows = div(row1, class_="row1") + div(row2, class_="row2") + div(row3, class_="row3")
    html = style(css) + main(rows)
    return html
