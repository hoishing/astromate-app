import streamlit as st
from const import BODIES, SESS
from datetime import date as Date
from datetime import datetime
from natal import Chart, Data, HouseSys, Stats
from natal.config import Display, Orb, ThemeType
from natal.const import ASPECT_NAMES
from streamlit_shortcuts import shortcut_button
from typing import Literal
from utils import all_cities, step


def general_opt():
    st.toggle("Show Statistics", key="show_stats")
    SESS.setdefault("house_sys", "Placidus")
    SESS.setdefault("theme_type", "dark")
    c1, c2 = st.columns(2)
    c1.selectbox("House System", HouseSys._member_names_, key="house_sys")
    c2.selectbox("Chart Theme", ThemeType.__args__, key="theme_type")


def orb_opt():
    def set_orbs(vals: list[int]):
        for aspect, val in zip(ASPECT_NAMES, vals):
            SESS.orb[aspect] = val

    SESS.setdefault("orb", Orb())
    for aspect in ASPECT_NAMES:
        st.number_input(
            label=aspect,
            value=SESS.orb[aspect],
            min_value=0,
            max_value=10,
            # actualize at change time, loop causes `aspect` stick to last value
            on_change=lambda asp: SESS.orb.update({asp: SESS[asp]}),
            args=(aspect,),  # actualize at create time
            key=aspect,
        )

    c1, c2, c3 = st.columns(3)
    c1.button(
        "disable",
        key="disable_orbs",
        use_container_width=True,
        on_click=lambda: set_orbs([0, 0, 0, 0, 0]),
    )
    c2.button(
        "transit",
        key="transit_orbs",
        use_container_width=True,
        on_click=lambda: set_orbs([2, 2, 2, 2, 1]),
    )
    c3.button(
        "default",
        key="default_orbs",
        use_container_width=True,
        on_click=lambda: set_orbs(Orb().model_dump().values()),
    )


def display_opt(num: int):
    display_num = f"display{num}"
    SESS.setdefault(display_num, Display())

    def toggle(body: str):
        body_n = f"{body}{num}"
        SESS[body_n] = SESS[display_num][body]
        st.toggle(
            body,
            key=body_n,
            # actualize at change time, won't stick to loop last value because its scoped by the enclosing function
            on_change=lambda: SESS[display_num].update({body: SESS[body_n]}),
        )

    def batch_update(num: int, opt: Literal["inner", "planets", "default"]):
        display = dict.fromkeys(BODIES, False)
        inner = ["asc", "sun", "moon", "mercury", "venus", "mars"]
        match opt:
            case "inner":
                display.update(dict.fromkeys(inner, True))
            case "planets":
                planets = inner + ["jupiter", "saturn", "uranus", "neptune", "pluto"]
                display.update(dict.fromkeys(planets, True))
            case "default":
                display = Display()

        SESS[f"display{num}"] = Display(**display)

    c1, c2 = st.columns(2)
    with c1:
        for body in BODIES[:10]:
            toggle(body)
    with c2:
        for body in BODIES[10:]:
            toggle(body)

    c1, c2 = st.columns(2)
    c1.button(
        "inner planets",
        key=f"inner_display{num}",
        use_container_width=True,
        on_click=lambda: batch_update(num, "inner"),
    )
    c2.button(
        "default",
        key=f"default_display{num}",
        use_container_width=True,
        on_click=lambda: batch_update(num, "default"),
    )


def input_ui(id: int):
    SESS.setdefault(f"name{id}", "" if id == 1 else "transit")
    SESS.setdefault(f"city{id}", None)
    with st.container(key=f"name-row{id}", horizontal=True):
        with st.container(key=f"name-city{id}", horizontal=True):
            name = st.text_input("Name", key=f"name{id}")
            city = st.selectbox(
                "City",
                all_cities(),
                key=f"city{id}",
                placeholder=" - ",
                format_func=lambda x: f"{x[0]} - {x[1]}",
            )
        with st.container(key=f"lat-lon{id}", horizontal=True):
            st.text_input("Latitude", key=f"lat{id}")
            st.text_input("Longitude", key=f"lon{id}")
    now = datetime.now()
    SESS.setdefault(f"date{id}", Date(2000, 1, 1) if id == 1 else now.date())
    SESS.setdefault(f"hr{id}", 13 if id == 1 else now.hour)
    SESS.setdefault(f"min{id}", 0 if id == 1 else now.minute)
    with st.container(key=f"date-row{id}", horizontal=True):
        st.date_input(
            "Date",
            max_value=Date(2300, 1, 1),
            min_value=Date(1800, 1, 1),
            format="YYYY-MM-DD",
            key=f"date{id}",
        )
        st.selectbox(
            "Hour",
            range(24),
            key=f"hr{id}",
        )
        st.selectbox(
            "Minute",
            range(60),
            key=f"min{id}",
            help="daylight saving time",
        )

    return name, city


def stepper_ui(id: int):
    with st.container(key="stepper"):
        st.write("")
        c1, c2, c3 = st.columns([3, 4, 3])
        with c2:
            unit = st.selectbox(
                "date adjustment",
                ["year", "month", "week", "day", "hour", "minute"],
                index=3,
                label_visibility="collapsed",
            )
        with c1:
            with st.container(key="prev-container", horizontal=True, horizontal_alignment="right"):
                shortcut_button(
                    "❮",
                    "alt+arrowleft",
                    hint=False,
                    on_click=step,
                    args=(id, unit, -1),
                    key="prev",
                )
        with c3:
            shortcut_button(
                "❯",
                "alt+arrowright",
                hint=False,
                on_click=step,
                args=(id, unit, 1),
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
