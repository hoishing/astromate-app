import streamlit as st
from const import BODIES, CHART_COLORS, HOUSE_SYS, LANGS, MODELS, ORBS, SESS
from datetime import date as Date
from datetime import datetime
from functools import reduce
from google.genai import Client, types
from natal import Chart, Data, Stats
from natal.config import Display
from natal.const import ASPECT_NAMES, PLANET_NAMES
from streamlit_shortcuts import shortcut_button
from textwrap import dedent
from utils import all_cities, all_timezones, consolidate_messages, i, set_lat_lon_dt_tz, step


def general_opt():
    c1, c2 = st.columns([3, 2])
    SESS.house_sys = SESS.get("house_sys", "Placidus")
    c1.selectbox(
        i("house-system"),
        HOUSE_SYS,
        key="house_sys",
        format_func=i,
    )
    c1.segmented_control(
        i("chart-color"),
        CHART_COLORS.keys(),
        key="theme_type",
        default=SESS.get("theme_type", "dark"),
        width="stretch",
        format_func=lambda x: CHART_COLORS[x],
    )
    c2.selectbox(
        i("language"),
        range(len(LANGS)),
        index=SESS.get("lang_num", 0),
        key="lang_num",
        format_func=lambda x: LANGS[x],
    )
    c2.segmented_control(
        i("statistics"),
        [True, False],
        key="show_stats",
        width="stretch",
        default=SESS.get("show_stats", False),
        format_func=lambda x: ":material/check: " if x else ":material/close:",
    )


def orb_opt():
    def set_orbs(vals: list[int]):
        for aspect, val in zip(ASPECT_NAMES, vals):
            SESS[aspect] = val

    def orb_input(aspect: str):
        SESS[aspect] = SESS.get(aspect, ORBS[aspect])
        st.number_input(label=i(aspect), min_value=0, max_value=10, key=aspect)

    c1, c2 = st.columns(2)
    with c1:
        for aspect in ASPECT_NAMES[:3]:
            orb_input(aspect)
    with c2:
        for aspect in ASPECT_NAMES[3:]:
            orb_input(aspect)

    c1, c2 = st.columns(2)
    c1.button(
        i("transit"),
        key="transit_orbs",
        use_container_width=True,
        on_click=lambda: set_orbs([2, 2, 2, 2, 1, 0]),
    )
    c2.button(
        i("default"),
        key="default_orbs",
        use_container_width=True,
        on_click=lambda: set_orbs(ORBS.values()),
    )


def display_opt(num: int):
    display_n = f"display{num}"

    def update_display(kind: str):
        presets = {
            "inner": PLANET_NAMES[:5],
            "classic": PLANET_NAMES[:7],
            "default": PLANET_NAMES,
        }
        planets = presets[kind] + ["asc"]
        SESS[display_n] = dict.fromkeys(Display.model_fields, False) | dict.fromkeys(planets, True)

    if display_n not in SESS:
        update_display("default")

    def toggle(body: str):
        body_n = f"{body}{num}"
        SESS[body_n] = SESS[display_n][body]
        st.toggle(
            i(body),
            key=body_n,
            # lambda don't have its own scope,
            # if not wrapped in a function, it will use the last value of for loop
            on_change=lambda: SESS[display_n].update({body: SESS[body_n]}),
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        for body in BODIES[:5]:
            toggle(body)
    with c2:
        for body in BODIES[5:10]:
            toggle(body)
    with c3:
        for body in BODIES[10:]:
            toggle(body)

    c1, c2, c3 = st.columns(3)
    c1.button(
        i("inner-planets"),
        key=f"inner_display{num}",
        use_container_width=True,
        on_click=lambda: update_display("inner"),
    )
    c2.button(
        i("classic"),
        key=f"classic_display{num}",
        use_container_width=True,
        on_click=lambda: update_display("classic"),
    )
    c3.button(
        i("default"),
        key=f"default_display{num}",
        use_container_width=True,
        on_click=lambda: update_display("default"),
    )


def input_ui(id: int):
    def reset_city():
        SESS[f"city{id}"] = None

    # name, city
    c1, c2 = st.columns(2)
    c1.text_input(
        i("name"),
        key=f"name{id}",
        value=SESS.get(f"name{id}", "" if id == 1 else "Transit"),
    )
    city = SESS.get(f"city{id}", None)
    c2.selectbox(
        i("city"),
        all_cities(),
        key=f"city{id}",
        index=all_cities().index(city) if city else None,
        placeholder=i("city-placeholder"),
        format_func=lambda x: f"{x[0]} - {x[1]}",
        on_change=set_lat_lon_dt_tz,
        args=(id,),
    )

    # lat, lon, tz
    SESS[f"lat{id}"] = SESS.get(f"lat{id}", None)
    SESS[f"lon{id}"] = SESS.get(f"lon{id}", None)
    SESS[f"tz{id}"] = SESS.get(f"tz{id}", None)
    c1, c2, c3 = st.columns(3)
    c1.number_input(
        i("latitude"),
        key=f"lat{id}",
        min_value=-89.99,
        max_value=89.99,
        on_change=reset_city,
    )
    c2.number_input(
        i("longitude"),
        key=f"lon{id}",
        min_value=-179.99,
        max_value=179.99,
        on_change=reset_city,
    )
    c3.selectbox(
        i("timezone"),
        all_timezones(),
        key=f"tz{id}",
        on_change=reset_city,
    )

    # date, hr, min
    now = datetime.now()
    with st.container(key=f"date-row{id}", horizontal=True):
        st.date_input(
            i("date"),
            value=SESS.get(f"date{id}", Date(2000, 1, 1) if id == 1 else now.date()),
            max_value=Date(2300, 1, 1),
            min_value=Date(1800, 1, 1),
            format="YYYY-MM-DD",
            key=f"date{id}",
        )
        st.selectbox(
            i("hour"),
            range(24),
            key=f"hr{id}",
            index=SESS.get(f"hr{id}", 13 if id == 1 else now.hour),
        )
        st.selectbox(
            i("minute"),
            range(60),
            key=f"min{id}",
            help="daylight saving time",
            index=SESS.get(f"min{id}", 0 if id == 1 else now.minute),
        )


def stepper_ui(id: int):
    with st.container(key="stepper"):
        st.write("")
        with st.container(
            key="stepper-container",
            horizontal=True,
            horizontal_alignment="center",
            vertical_alignment="center",
        ):
            SESS["stepper-unit"] = SESS.get("stepper-unit", "day")
            shortcut_button(
                "❮",
                # ":material/arrow_back_ios_new:",
                "alt+arrowleft",
                hint=False,
                on_click=step,
                args=(id, SESS["stepper-unit"], -1),
                key="prev",
            )

            st.segmented_control(
                i("adjustment"),
                ["year", "month", "week", "day", "hour", "minute"],
                width="content",
                label_visibility="collapsed",
                format_func=lambda x: i(x),
                key="stepper-unit",
            )

            shortcut_button(
                # ":material/arrow_forward_ios:",
                "❯",
                "alt+arrowright",
                hint=False,
                on_click=step,
                args=(id, SESS["stepper-unit"], 1),
                key="next",
            )


def chart_ui(data1: Data, data2: Data = None):
    st.write("")
    chart = Chart(data1=data1, data2=data2, width=SESS.chart_size)
    with st.container(key="chart_svg"):
        st.markdown(chart.svg, unsafe_allow_html=True)


def stats_ui(data1: Data, data2: Data = None):
    stats = Stats(data1=data1, data2=data2)
    st.markdown(stats.full_report("html"), unsafe_allow_html=True)
    st.write("")
