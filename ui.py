import streamlit as st
from const import BODIES, SESS
from datetime import date as Date
from datetime import datetime, timedelta
from natal import Chart, Data, HouseSys, Stats
from natal.config import Config, Display, Orb, ThemeType
from natal.const import ASPECT_NAMES
from streamlit_shortcuts import shortcut_button
from typing import Literal
from utils import get_cities, get_dt, utc_of


def general_opt():
    st.toggle("Show Statistics", key="show_stats")
    SESS.setdefault("house_sys", "Placidus")
    SESS.setdefault("theme_type", "dark")
    c1, c2 = st.columns(2)
    c1.selectbox("House System", HouseSys._member_names_, key="house_sys")
    c2.selectbox("Chart Theme", ThemeType.__args__, key="theme_type")
    # st.slider("Chart Size", 300, 1200, 600, 50, key="chart_size")


def orb_opt():
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
    display_n = f"display{num}"
    SESS.setdefault(display_n, Display())

    def toggle(body: str):
        body_n = f"{body}{num}"
        SESS[body_n] = SESS[display_n][body]
        st.toggle(
            body,
            key=body_n,
            # actualize at change time, won't stick to loop last value because its scoped by the enclosing function
            on_change=lambda: SESS[display_n].update({body: SESS[body_n]}),
        )

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
        on_click=lambda: set_displays(num, "inner"),
    )
    c2.button(
        "default",
        key=f"default_display{num}",
        use_container_width=True,
        on_click=lambda: set_displays(num, "default"),
    )


# options utils ======================================================


def set_orbs(vals: list[int]):
    for aspect, val in zip(ASPECT_NAMES, vals):
        SESS.orb[aspect] = val


def set_displays(num: int, opt: Literal["inner", "planets", "default"]):
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


# chart ui ======================================================


def input_ui(id: int):
    SESS.setdefault(f"name{id}", "" if id == 1 else "transit")
    SESS.setdefault(f"city{id}", None)
    c1, c2 = st.columns(2)
    name = c1.text_input("Name", key=f"name{id}")
    city = c2.selectbox(
        "City", get_cities().index, key=f"city{id}", help="type to search"
    )
    now = datetime.now()
    SESS.setdefault(f"date{id}", Date(2000, 1, 1) if id == 1 else now.date())
    SESS.setdefault(f"hr{id}", 13 if id == 1 else now.hour)
    SESS.setdefault(f"min{id}", 0 if id == 1 else now.minute)
    c1, c2, c3 = st.columns(3)
    c1.date_input(
        "Date",
        max_value=Date(2300, 1, 1),
        min_value=Date(1800, 1, 1),
        format="YYYY-MM-DD",
        key=f"date{id}",
    )
    c2.selectbox(
        "Hour",
        range(24),
        key=f"hr{id}",
    )
    c3.selectbox(
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
            with st.container(
                key="prev-container", horizontal=True, horizontal_alignment="right"
            ):
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


# chart utils ======================================================


def step(chart_id: int, unit: str, delta: Literal[1, -1]):
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


def data_obj(
    name1: str,
    city1: str,
    name2: str = None,
    city2: str = None,
):
    def get_params(id: int, city: str) -> dict:
        city_info = get_cities().loc[city]
        lat_lon = city_info[["lat", "lon"]].to_dict()
        lat_lon["utc_dt"] = utc_of(get_dt(id), city_info["timezone"])
        return lat_lon

    house_sys = HouseSys[SESS["house_sys"]]
    orb = SESS.orb
    display1 = {body: SESS[f"{body}1"] for body in BODIES}

    data1 = Data(
        name=name1,
        **get_params(1, city1),
        config=Config(
            house_sys=house_sys, theme_type=SESS.theme_type, orb=orb, display=display1
        ),
    )

    if name2 and city2:
        display2 = {body: SESS[f"{body}2"] for body in BODIES}
        orb2 = Orb(**{aspect: 0 for aspect in ASPECT_NAMES})
        data2 = Data(
            name=name2,
            **get_params(2, city2),
            config=Config(house_sys=house_sys, orb=orb2, display=display2),
        )
    else:
        data2 = None

    return data1, data2


# no use now
def input_status() -> tuple[str, bool, bool, str, str, str, str]:
    name1 = SESS.get("name1")
    city1 = SESS.get("city1")
    name2 = SESS.get("name2")
    city2 = SESS.get("city2")
    filename = f"{name1}_{name2}" if (name2 and city2) else name1
    return filename, name1, city1, name2, city2
