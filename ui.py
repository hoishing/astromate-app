import streamlit as st
from const import ASPECTS, BODIES, CHART_COLORS, HOUSE_SYS, LANGS, SESS
from datetime import date as Date
from datetime import datetime
from natal import Chart, Data, Stats
from natal.config import Display, Orb
from streamlit_shortcuts import shortcut_button
from typing import Literal
from utils import all_cities, all_timezones, i, set_lat_lon_dt_tz, step


def general_opt():
    SESS.setdefault("lang", "English")
    SESS.setdefault("house_sys", "Placidus")
    SESS.setdefault("theme_type", "dark")
    SESS.setdefault("show_stats", False)
    c1, c2 = st.columns([3, 2])
    c1.selectbox(
        "House System",
        HOUSE_SYS,
        key="house_sys",
        format_func=lambda x: x.replace("_", " "),
    )
    c1.segmented_control(
        "Chart Color",
        CHART_COLORS,
        key="theme_type",
        width="stretch",
        format_func=lambda x: CHART_COLORS[x],
    )
    c2.selectbox(
        "Language",
        range(len(LANGS)),
        key="lang_num",
        index=0,
        format_func=lambda x: LANGS[x],
    )
    c2.segmented_control(
        "Statistics",
        [True, False],
        key="show_stats",
        width="stretch",
        format_func=lambda x: ":material/check: " if x else ":material/close:",
    )


def orb_opt():
    def set_orbs(vals: list[int]):
        for aspect, val in zip(ASPECTS, vals):
            SESS.orb[aspect] = val

    SESS.setdefault("orb", Orb())
    for aspect in ASPECTS:
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
    default_display = Display(asc_node=False, mc=False)
    inner_display = Display(
        **dict.fromkeys("asc_node mc jupiter saturn uranus neptune pluto".split(), False)
    )
    SESS.setdefault(display_num, default_display)

    def toggle(body: str):
        body_n = f"{body}{num}"
        SESS[body_n] = SESS[display_num][body]
        st.toggle(
            i(body),
            key=body_n,
            # actualize at change time, won't stick to loop last value because its scoped by the enclosing function
            on_change=lambda: SESS[display_num].update({body: SESS[body_n]}),
        )

    def button_opts(opt: Literal["inner", "default"]):
        display = inner_display if opt == "inner" else default_display
        label = "inner planets" if opt == "inner" else "default"
        return dict(
            label=label,
            key=f"{opt}_display{num}",
            use_container_width=True,
            on_click=lambda: SESS[display_num].update(display),
        )

    c1, c2 = st.columns(2)
    with c1:
        for body in BODIES[:7]:
            toggle(body)
    with c2:
        for body in BODIES[7:]:
            toggle(body)

    c1, c2 = st.columns(2)
    c1.button(**button_opts("inner"))
    c2.button(**button_opts("default"))


def input_ui(id: int):
    SESS.setdefault(f"name{id}", "" if id == 1 else "Transit")
    SESS.setdefault(f"city{id}", None)

    def reset_city():
        SESS[f"city{id}"] = None

    c1, c2 = st.columns(2)
    c1.text_input("Name", key=f"name{id}")
    c2.selectbox(
        "City",
        all_cities(),
        key=f"city{id}",
        placeholder=i("city-placeholder"),
        format_func=lambda x: f"{x[0]} - {x[1]}",
        on_change=set_lat_lon_dt_tz,
        args=(id,),
    )
    c1, c2, c3 = st.columns(3)
    c1.number_input(
        "Latitude",
        key=f"lat{id}",
        min_value=-89.99,
        max_value=89.99,
        value=None,
        on_change=reset_city,
    )
    c2.number_input(
        "Longitude",
        key=f"lon{id}",
        min_value=-179.99,
        max_value=179.99,
        value=None,
        on_change=reset_city,
    )
    c3.selectbox(
        "Timezone",
        all_timezones(),
        key=f"tz{id}",
        index=None,
        format_func=lambda x: x[0],
    )
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
        st.selectbox("Hour", range(24), key=f"hr{id}")
        st.selectbox("Minute", range(60), key=f"min{id}", help="daylight saving time")


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
