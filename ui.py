import pandas as pd
import streamlit as st
from archive import (
    DEFAULT_GENERAL_OPTS,
    create_user,
    fetch_user_record,
    load_chart,
    save_chart,
)
from const import HOUSE_SYS, LANGS, ORBS, PDF_COLOR, ROW_HEIGHT, SESS, VAR
from datetime import date as Date
from natal import Chart, Data
from natal.config import Display
from natal.const import ASPECT_NAMES, PLANET_NAMES
from streamlit.column_config import DatetimeColumn, LinkColumn
from utils import (
    all_charts,
    all_cities,
    all_timezones,
    cities_db,
    data_db,
    i,
    new_chat,
    pdf_html,
    pdf_io,
    scroll_to_bottom,
    stats_html,
    step,
    sync,
    sync_nullable,
)


def general_opt():
    """general options from database, or show default options if user not logged in"""

    # print("general_opt start:", datetime.now())
    def update_db(key: str):
        if st.user.is_logged_in:
            sync(key)
            sql = f"UPDATE users SET {key} = ? WHERE email = ?"
            cursor = data_db().cursor()
            cursor.execute(sql, (VAR[key], st.user.email))
            data_db().commit()

    if st.user.is_logged_in:
        # get user options from db
        if user_record := fetch_user_record(st.user.email):
            # user found, set general options from db
            for field in DEFAULT_GENERAL_OPTS:
                VAR[field] = user_record[field]
        else:
            # create user with default options
            create_user([st.user.email] + [VAR[field] for field in DEFAULT_GENERAL_OPTS])

    c1, c2 = st.columns([3, 2])

    SESS.house_sys = VAR.house_sys
    c1.selectbox(
        i("house-system"),
        options=HOUSE_SYS,
        key="house_sys",
        format_func=i,
        on_change=lambda: update_db("house_sys"),
    )

    SESS.lang_num = VAR.lang_num
    c2.selectbox(
        i("language"),
        options=range(len(LANGS)),
        key="lang_num",
        format_func=lambda x: LANGS[x],
        on_change=lambda: update_db("lang_num"),
    )

    c1, c2, c3 = st.columns(3)

    SESS.pdf_color = VAR.pdf_color
    c1.segmented_control(
        i("pdf-color"),
        options=PDF_COLOR,
        key="pdf_color",
        width="stretch",
        format_func=lambda x: PDF_COLOR[x],
        on_change=lambda: update_db("pdf_color"),
    )

    SESS.show_stats = VAR.show_stats
    c2.segmented_control(
        i("statistics"),
        options=[True, False],
        key="show_stats",
        width="stretch",
        format_func=lambda x: ":material/check: " if x else ":material/close:",
        on_change=lambda: update_db("show_stats"),
    )

    SESS.ai_chat = VAR.ai_chat
    c3.segmented_control(
        "AI",
        options=[True, False],
        key="ai_chat",
        width="stretch",
        format_func=lambda x: ":material/check: " if x else ":material/close:",
        on_change=lambda: update_db("ai_chat"),
    )


def orb_opt():
    """orb settings"""

    def orb_input(aspect: str):
        SESS[aspect] = VAR[aspect]
        st.number_input(
            label=i(aspect),
            min_value=0,
            max_value=10,
            key=aspect,
            on_change=lambda: sync(aspect),
        )

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
        on_click=lambda: VAR.update(dict(zip(ASPECT_NAMES, [2, 2, 2, 2, 1, 0]))),
    )
    c2.button(
        i("default"),
        key="default_orbs",
        use_container_width=True,
        on_click=lambda: VAR.update(ORBS),
    )


def display_opt(id: int):
    """options for displaying a celestial body or not"""

    def update_display(id: int, kind: str):
        presets = {
            "inner": PLANET_NAMES[:5],
            "classic": PLANET_NAMES[:7],
            "default": PLANET_NAMES,
        }
        planets = presets[kind] + ["asc"]
        data = dict.fromkeys(Display.model_fields, False) | dict.fromkeys(planets, True)
        for body in data:
            VAR[f"{body}{id}"] = data[body]

    def toggle(body: str):
        key = f"{body}{id}"
        SESS[key] = VAR[key]
        # print(key, VAR[key])
        st.toggle(
            i(body),
            key=key,
            on_change=lambda: sync(key),
        )

    c1, c2, c3 = st.columns(3)
    bodies = list(Display.model_fields)
    with c1:
        for body in bodies[:7]:
            toggle(body)
    with c2:
        for body in bodies[7:14]:
            toggle(body)
    with c3:
        for body in bodies[14:]:
            toggle(body)

    c1, c2, c3 = st.columns(3)
    c1.button(
        i("inner-planets"),
        key=f"inner_display{id}",
        use_container_width=True,
        on_click=lambda: update_display(id, "inner"),
    )
    c2.button(
        i("classic"),
        key=f"classic_display{id}",
        use_container_width=True,
        on_click=lambda: update_display(id, "classic"),
    )
    c3.button(
        i("default"),
        key=f"default_display{id}",
        use_container_width=True,
        on_click=lambda: update_display(id, "default"),
    )


def input_ui(id: int):
    """natal data input ui"""

    def set_lat_lon_dt_tz(id: int):
        """return lat, lon, utc datetime from a chart input ui"""
        city = f"city{id}"
        sync_nullable(city)
        cursor = cities_db().cursor()
        cursor.execute("SELECT lat, lon, timezone FROM cities WHERE name = ? and country = ?", VAR[city])
        lat, lon, timezone = cursor.fetchone()
        VAR[f"lat{id}"] = lat
        VAR[f"lon{id}"] = lon
        VAR[f"tz{id}"] = timezone

    def name_and_city(id: int):
        c1, c2 = st.columns(2)

        name_key = f"name{id}"
        SESS[name_key] = VAR[name_key]
        c1.text_input(
            i("name"),
            key=name_key,
            on_change=lambda: sync(name_key),
        )

        city_key = f"city{id}"
        SESS[city_key] = VAR[city_key]
        c2.selectbox(
            i("city"),
            all_cities(),
            key=city_key,
            placeholder=i("city-placeholder"),
            format_func=lambda city_tuple: f"{city_tuple[0]} - {city_tuple[1]}",
            on_change=lambda: set_lat_lon_dt_tz(id),
        )

    def lat_lon_tz(id: int):
        c1, c2, c3 = st.columns(3)
        lat, lon, tz = f"lat{id}", f"lon{id}", f"tz{id}"

        SESS[lat] = VAR[lat]
        c1.number_input(
            i("latitude"),
            key=lat,
            min_value=-89.99,
            max_value=89.99,
            on_change=lambda: sync(lat),
        )

        SESS[lon] = VAR[lon]
        c2.number_input(
            i("longitude"),
            key=lon,
            min_value=-179.99,
            max_value=179.99,
            on_change=lambda: sync(lon),
        )

        SESS[tz] = VAR[tz]
        c3.selectbox(
            i("timezone"),
            all_timezones(),
            key=tz,
            on_change=lambda: sync(tz),
        )

    def date_hr_min(id: int):
        with st.container(key=f"date-row{id}", horizontal=True):
            date_key = f"date{id}"
            SESS[date_key] = VAR[date_key]
            st.date_input(
                i("date"),
                max_value=Date(2300, 1, 1),
                min_value=Date(1800, 1, 1),
                format="YYYY-MM-DD",
                key=date_key,
                on_change=lambda: sync(date_key),
            )

            hr_key = f"hr{id}"
            SESS[hr_key] = VAR[hr_key]
            st.selectbox(
                i("hour"),
                range(24),
                key=hr_key,
                help=i("daylight-saving-time"),
                on_change=lambda: sync(hr_key),
            )

            min_key = f"min{id}"
            SESS[min_key] = VAR[min_key]
            st.selectbox(
                i("minute"),
                range(60),
                key=min_key,
                on_change=lambda: sync(min_key),
            )

    name_and_city(id)
    lat_lon_tz(id)
    date_hr_min(id)


def utils_ui(id: int, data1: Data, data2: Data | None):
    st.write("")
    with st.container(
        key="utils-container",
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center",
    ):
        stepper_options = ["year", "month", "week", "day", "hour", "minute"]
        st.button(
            "",
            icon=":material/arrow_left:",
            on_click=lambda: step(id, -1),
            key="prev",
            help=i("prev") + i(VAR.stepper_unit),
        )

        SESS["stepper_unit"] = VAR["stepper_unit"]
        st.selectbox(
            i("adjustment"),
            stepper_options,
            label_visibility="collapsed",
            format_func=lambda x: i(x),
            key="stepper_unit",
            width=90,
            on_change=lambda: sync("stepper_unit"),
        )

        st.button(
            "",
            icon=":material/arrow_right:",
            on_click=lambda: step(id, 1),
            key="next",
            help=i("next") + i(VAR.stepper_unit),
        )

        if st.user.is_logged_in:
            st.button(
                "",
                icon=":material/save:",
                key="save",
                on_click=lambda: st.toast(i("chart-created"), icon=":material/check:")
                if save_chart(st.user.email) == "create"
                else st.toast(i("chart-updated"), icon=":material/check:"),
                help=i("save-chart"),
            )
        else:
            st.button(
                "",
                icon=":material/login:",
                key="login-small-button",
                on_click=st.login,
                help=i("login"),
            )

        with st.container(width=50, key="print-container"):
            with st.empty():
                if st.button("", icon=":material/print:", key="pdf-button", help=i("gen-pdf")):
                    with st.spinner("", width="stretch"):
                        html = pdf_html(data1, data2)
                        pdf = pdf_io(html)
                    filename = f"{VAR.name1}_{VAR.name2}" if VAR.name2 else VAR.name1
                    st.download_button(
                        "",
                        icon=":material/download:",
                        data=pdf,
                        file_name=f"{filename}.pdf",
                        mime="application/pdf",
                        help=i("download-pdf"),
                    )


def chart_ui(data1: Data, data2: Data = None):
    st.write("")
    chart = Chart(data1=data1, data2=data2, width=VAR.chart_size)
    with st.container(key="chart_svg"):
        st.markdown(chart.svg, unsafe_allow_html=True)
    # reset chat history when loading new chart
    VAR.chat = None


def stats_ui(data1: Data, data2: Data | None):
    with st.container(key="stats-ui"):
        html = stats_html(data1, data2)
        st.markdown(html, unsafe_allow_html=True)


def ai_ui(data1: Data, data2: Data | None) -> None:
    # Initialize new chat only when new chart is loaded, this keeps the history during rerun
    VAR.chat = VAR.get("chat", new_chat(data1, data2))

    # Display chat history
    avatar = {"user": "👤", "assistant": "💫"}
    for message in VAR.chat.messages[1:]:
        role = message["role"]
        text = message["content"]
        with st.chat_message(role, avatar=avatar[role]):
            st.markdown(text)

    # Accept user input
    if prompt := st.chat_input(i("chat-placeholder")):
        # Display user message
        with st.chat_message("user", avatar=avatar["user"]):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant", avatar=avatar["assistant"]):
            try:
                response = VAR.chat.send_message_stream(prompt)

                with st.spinner(f"{i('thinking')}...", show_time=True):
                    scroll_to_bottom()
                    st.write_stream(chunk for chunk in response)
                    scroll_to_bottom()

            except Exception as e:
                st.error(e)
                st.stop()


def saved_charts_ui():
    def on_select(data: pd.DataFrame):
        selected = SESS.saved_charts.selection.cells
        if selected:
            row = data.iloc[selected[0][0]]  # first value of first cell
            load_chart(row.to_dict())

    st.subheader(i("saved-charts"))
    data = all_charts()
    if data is None:
        st.info(i("no-saved-charts"))
    else:
        height = (len(data) + 1) * ROW_HEIGHT + 2
        column_config = {f"{prop}{num}": None for num in "12" for prop in ["lat", "lon", "tz"]}
        column_config |= {f"name{num}": i("birth") for num in "12"}
        column_config |= {f"city{num}": i("city") for num in "12"}
        column_config |= {f"dt{num}": DatetimeColumn(i("date"), format="YYYY-MM-DD HH:MM") for num in "12"}
        column_config |= {prop: None for prop in ["theme_type", "house_sys"]}
        column_config |= {aspect: None for aspect in ASPECT_NAMES}
        column_config |= {f"{body}{num}": None for num in "12" for body in Display.model_fields}
        column_config |= {"hash": LinkColumn("", display_text=":material/delete:")}
        st.dataframe(
            data,
            hide_index=True,
            height=height,
            column_config=column_config,
            column_order=["name1", "city1", "dt1", "name2", "city2", "dt2", "hash"],
            row_height=ROW_HEIGHT,
            key="saved_charts",
            selection_mode="single-cell",
            on_select=lambda: on_select(data),
        )
