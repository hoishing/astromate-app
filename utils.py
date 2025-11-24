import json
import logging
import pandas as pd
import sqlite3
import streamlit as st
from const import DEFAULT_INPUTS, I18N, ORBS, SESS
from datetime import datetime, timedelta, timezone
from io import BytesIO
from natal import Chart, Config, Data, Stats
from natal.config import Display
from natal.const import ASPECT_NAMES
from pathlib import Path
from streamlit.components.v2 import component as custom_component
from tagit import div, main, style, table, td, tr
from typing import Iterable, Literal
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from zoneinfo import ZoneInfo

# suppress fontTools warnings
logging.getLogger("fontTools").setLevel(logging.ERROR)


def lang_num() -> int:
    """get language number from subdomain"""
    # explicit path parameter
    match st.context.url.split("/")[-1]:
        case "en":
            return 0
        case "zh":
            return 1
    # implicit browser locale
    locale = st.context.locale
    match locale[:2].lower():
        case "zh":
            return 1
        case _:
            return 0


def debug_print(key: str | None = None) -> None:
    SESS.rerun_cnt += 1
    val = f"{key}: {SESS[key]}" if key else ""
    print(SESS.rerun_cnt, val)


def i(key: str) -> str:
    """get i18n string"""
    return I18N[key][lang_num()]


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


@st.cache_data
def cities_df() -> pd.DataFrame:
    return pd.read_csv("cities.csv")


@st.cache_resource
def data_db() -> sqlite3.Connection:
    return sqlite3.connect("data.db", check_same_thread=False)


@st.cache_data
def all_timezones() -> list[str]:
    return cities_df()["tz"].unique()


def natal_data(id: int) -> Data:
    """return natal data from a chart input ui"""
    display = {key: SESS[f"{key}{id}"] for key in Display.model_fields}
    aspects = {aspect: SESS[aspect] for aspect in ASPECT_NAMES}
    hse_1st_char = SESS.house_sys[0]
    data = Data(
        name=SESS[f"name{id}"],
        lat=SESS[f"lat{id}"],
        lon=SESS[f"lon{id}"],
        utc_dt=utc_of(id),
        config=Config(house_sys=hse_1st_char, orb=aspects, display=display),
    )
    is_solar_return = id == 1 and SESS.chart_type == "solar_return_page"
    return data.solar_return(target_yr=SESS.solar_return_year) if is_solar_return else data


def step(chart_id: int, delta: Literal[1, -1]):
    """step implementation for stepper ui"""
    dt = get_dt(chart_id)
    unit = SESS.stepper_unit
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


def charts_df() -> pd.DataFrame | None:
    def calculate_age(birth: str) -> str:
        birth_dt = pd.to_datetime(birth).replace(tzinfo=timezone.utc)
        today = pd.Timestamp.now(tz="UTC")
        age = today.year - birth_dt.year
        if (today.month, today.day) < (birth_dt.month, birth_dt.day):
            age -= 1
        return str(age)

    sql = (
        "select data, hash from charts where email = ? and chart_type = ? order by updated_at desc"
    )
    cursor = data_db().cursor()
    cursor.execute(sql, (st.user.email, SESS.chart_type))
    all_data = cursor.fetchall()
    if not all_data:
        return None

    df = pd.DataFrame([{**json.loads(d), "hash": h} for (d, h) in all_data])
    if len(df) == 0:
        return None

    df.set_index("hash", inplace=True, drop=False)
    df.rename(columns={"hash": "delete"}, inplace=True)
    df["delete"] = "?delete=" + df["delete"]
    df["age1"] = df["dt1"].apply(calculate_age)
    df["age2"] = df["dt2"].apply(calculate_age)
    df["solar_return_year"] = df["solar_return_year"].astype(str)
    return df


def reset_inputs() -> bool:
    for key, val in DEFAULT_INPUTS.items():
        SESS[key] = val
    SESS.date2 = (
        datetime.now(ZoneInfo(st.context.timezone)).date()
        if SESS.chart_type == "transit_page"
        else datetime(2000, 1, 1).date()
    )
    SESS.ai = None
    return True


def update_orbs() -> bool:
    if SESS.chart_type == "transit_page":
        SESS.update(dict(zip(ASPECT_NAMES, [2, 2, 2, 2, 1, 0])))
    elif SESS.chart_type == "synastry_page":
        SESS.update(dict(zip(ASPECT_NAMES, [3, 3, 3, 3, 2, 0])))
    else:
        SESS.update(ORBS)
    return True


def is_form_valid(num: int) -> bool:
    for name in ["name", "tz", "date"]:
        key = f"{name}{num}"
        if not SESS.get(key):
            return False
    for name in ["lat", "lon"]:
        key = f"{name}{num}"
        if SESS.get(key) is None:
            return False
    return True


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
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(fp, font_config=font_config)
    return fp


def local_time_label() -> str:
    match SESS.chart_type:
        case "birth_page" | "synastry_page":
            return i("birth_time")
        case "transit_page":
            return i("local_time")
        case "solar_return_page":
            return i("solar_return_time")


def stats_html(data1: Data, data2: Data = None):
    stats = Stats(
        data1=data1, data2=data2, city1=SESS.city1, city2=SESS.city2, tz1=SESS.tz1, tz2=SESS.tz2
    )
    basic_info_headers = [i("name"), i("city"), i("coordinates"), local_time_label()]
    basic_info_title = f"{i(SESS.chart_type)} - {i('basic_info')}"
    basic_info = html_section(basic_info_title, stats.basic_info(basic_info_headers))

    ele_mod_headers = [i("fire"), i("air"), i("water"), i("earth"), i("sum")]
    ele_mod_row = [i("cardinal"), i("fixed"), i("mutable"), i("sum")]
    ele_mod_polor = [i("polarity"), i("pos"), i("neg")]
    ele_mod_grid = stats.elements_vs_modalities(ele_mod_headers, ele_mod_row, ele_mod_polor)
    ele_mod = html_section(i("elements_vs_modalities"), ele_mod_grid)

    quad_hemi_headers = [i("eastern"), i("western"), i("northern"), i("southern"), i("sum")]
    quad_hemi_grid = stats.quadrants_vs_hemispheres(quad_hemi_headers)
    quad_hemi = html_section(i("quad_vs_hemi"), quad_hemi_grid)

    body_headers = [i("body"), i("sign"), i("house"), i("dignity")]
    dignity_labels = [i("domicile"), i("exaltation"), i("fall"), i("detriment")]
    bodies_grid = stats.celestial_bodies(1, body_headers, dignity_labels)
    user_name = f" - {data1.name}" if data2 else ""
    bodies = html_section(i("celestial_body") + user_name, bodies_grid)
    houses_title = f"{i('houses')} - {i(SESS.house_sys)}"

    if data2:
        # bodies 2
        bodies_grid2 = stats.celestial_bodies(2, body_headers, dignity_labels)
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

    basic_info_title = f"{i(SESS.chart_type)} - {i('basic_info')}"
    basic_info_headers = [i("name"), i("city"), i("coordinates"), local_time_label()]
    ele_vs_mod_headers = ["🜂", "🜁", "🜄", "🜃", "∑"]
    ele_vs_mod_row_label = ["⟑", "⊟", "𛰣", "∑"]
    ele_vs_mod_polarity_label = ["◐", "+", "-"]
    quad_vs_hemi_headers = [i("eastern"), i("western"), i("northern"), i("southern"), "∑"]
    body_headers = [i("body"), i("sign"), i("house"), i("dignity")]
    dignity_labels = ["⏫", "🔼", "⏬", "🔽"]
    aspects_title = i("aspects")
    signs_title = i("signs")
    signs_headers = [i("sign")]
    houses_title = f"{i('houses')} - {i(SESS.house_sys)}"
    if data2:
        ele_vs_mod_title = i("elements_vs_modalities") + f" - {data1.name}"
        quad_vs_hemi_title = i("quad_vs_hemi") + f" - {data1.name}"
        body_title1 = i("celestial_body") + f" - {data1.name}"
        body_title2 = i("celestial_body") + f" - {data2.name}"
        signs_headers = [i("sign"), data1.name, data2.name, "∑"]
        houses_headers = [i("house"), i("cusp"), data1.name, data2.name, "∑"]
    else:
        ele_vs_mod_title = i("elements_vs_modalities")
        quad_vs_hemi_title = i("quad_vs_hemi")
        body_title1 = i("celestial_body")
        signs_headers = [i("sign"), i("bodies"), "∑"]
        houses_headers = [i("house"), i("cusp"), i("bodies"), "∑"]

    orb_title = i("orbs")
    orb_headers = [i("aspect"), i("orb")]

    row1 = div(
        html_section(basic_info_title, stats.basic_info(basic_info_headers))
        + html_section(
            ele_vs_mod_title,
            stats.elements_vs_modalities(
                headers=ele_vs_mod_headers,
                row_label=ele_vs_mod_row_label,
                polarity_label=ele_vs_mod_polarity_label,
                pdf=True,
            ),
        )
        + html_section(
            quad_vs_hemi_title,
            stats.quadrants_vs_hemispheres(headers=quad_vs_hemi_headers, pdf=True),
        ),
        class_="info_col",
    ) + div(chart.svg, class_="chart")

    body_params = {"headers": body_headers, "dignity_labels": dignity_labels, "pdf": True}
    row2 = html_section(body_title1, stats.celestial_bodies(1, **body_params))

    if stats.data2:
        row2 += html_section(body_title2, stats.celestial_bodies(2, **body_params))

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


# custom components ============================================================

scroll_to_bottom = custom_component(
    "scroll_to_bottom",
    js="""
    export default function(component) {
        const target = document.querySelector(".stMainBlockContainer");
        target.scrollTo({
            top: target.scrollHeight,
            behavior: "smooth",
        });
        // console.log(target.scrollHeight);
    }
    """,
)


screenwidth_detector = custom_component(
    "screen_width_detector",
    js=Path("screenwidth_detector.js").read_text(),
)
