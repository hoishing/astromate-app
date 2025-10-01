import pandas as pd
import streamlit as st
from const import BODIES, CHART_COLORS, HIST_COL_CONFIG, HOUSE_SYS, LANGS, ORBS, ROW_HEIGHT, SESS
from datetime import date as Date
from datetime import datetime
from natal import Chart, Data, Stats
from natal.config import Display
from natal.const import ASPECT_NAMES, PLANET_NAMES
from streamlit_shortcuts import shortcut_button
from utils import all_cities, all_timezones, i, new_chat, scroll_to_bottom, set_lat_lon_dt_tz, step


def general_opt():
    c1, c2 = st.columns([3, 2])
    SESS.house_sys = SESS.get("house_sys", "Placidus")
    c1.selectbox(
        i("house-system"),
        HOUSE_SYS,
        key="house_sys",
        format_func=i,
    )
    c2.selectbox(
        i("language"),
        range(len(LANGS)),
        index=SESS.get("lang_num", 0),
        key="lang_num",
        format_func=lambda x: LANGS[x],
    )

    c1, c2, c3 = st.columns([3, 2, 2])
    c1.segmented_control(
        i("chart-color"),
        CHART_COLORS.keys(),
        key="theme_type",
        default=SESS.get("theme_type", "dark"),
        width="stretch",
        format_func=lambda x: CHART_COLORS[x],
    )
    c2.segmented_control(
        i("statistics"),
        [True, False],
        key="show_stats",
        width="stretch",
        default=SESS.get("show_stats", False),
        format_func=lambda x: ":material/check: " if x else ":material/close:",
    )
    c3.segmented_control(
        "AI",
        [True, False],
        key="ai_chat",
        width="stretch",
        default=SESS.get("ai_chat", True),
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
        SESS[display_n] = Display(
            **(dict.fromkeys(Display.model_fields, False) | dict.fromkeys(planets, True))
        )

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


def utils_ui(id: int):
    st.write("")
    with st.container(
        key="utils-container",
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center",
        # gap=None,
    ):
        SESS["stepper-unit"] = SESS.get("stepper-unit", "day")
        shortcut_button(
            # "❮",
            ":material/arrow_back_ios_new:",
            "alt+arrowleft",
            hint=False,
            on_click=step,
            args=(id, SESS["stepper-unit"], -1),
            key="prev",
        )

        st.selectbox(
            i("adjustment"),
            ["year", "month", "week", "day", "hour", "minute"],
            # index=3,
            label_visibility="collapsed",
            format_func=lambda x: i(x),
            key="stepper-unit",
            width=90,
        )

        shortcut_button(
            ":material/arrow_forward_ios:",
            # "❯",
            "alt+arrowright",
            hint=False,
            on_click=step,
            args=(id, SESS["stepper-unit"], 1),
            key="next",
        )

        def save_chart():
            if st.user.is_logged_in:
                pass
            else:
                st.login()

        st.button("", icon=":material/save:", key="save", on_click=save_chart)
        st.button("", icon=":material/print:", key="print", on_click=lambda: ...)


def chart_ui(data1: Data, data2: Data = None):
    st.write("")
    chart = Chart(data1=data1, data2=data2, width=SESS.chart_size)
    with st.container(key="chart_svg"):
        st.markdown(chart.svg, unsafe_allow_html=True)
    if "chat" in SESS:
        del SESS["chat"]


def stats_ui(data1: Data, data2: Data = None):
    stats = Stats(data1=data1, data2=data2)
    st.markdown(stats.full_report("html"), unsafe_allow_html=True)
    st.write("")


def ai_ui(data1: Data, data2: Data = None) -> None:
    # Initialize new chat for each chart
    SESS.chat = SESS.get("chat", new_chat(data1, data2))

    # Display chat history
    avatar = {"user": "👤", "assistant": "💫"}
    for message in SESS.chat.messages[1:]:
        role = message["role"]
        text = message["content"]
        with st.chat_message(role, avatar=avatar[role]):
            st.markdown(text)

    # Accept user input
    if prompt := st.chat_input("chat about the astrological chart..."):
        # Display user message
        with st.chat_message("user", avatar=avatar["user"]):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            try:
                response = SESS.chat.send_message_stream(prompt)

                with st.spinner(f"{i('thinking')}...", show_time=True):
                    scroll_to_bottom()
                    st.write_stream(chunk for chunk in response)
                    scroll_to_bottom()

            except Exception as e:
                st.error(e)
                st.stop()


def saved_charts_ui():
    st.subheader(i("saved-charts"))
    df = pd.read_csv("mock.csv", usecols=HIST_COL_CONFIG.keys())
    df1 = df.iloc[:3]
    height = (len(df1) + 1) * ROW_HEIGHT + 2
    st.dataframe(
        df1, hide_index=True, column_config=HIST_COL_CONFIG, height=height, row_height=ROW_HEIGHT
    )
