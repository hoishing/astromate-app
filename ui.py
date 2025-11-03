import pandas as pd
import streamlit as st
from ai import new_chat
from archive import (
    DEFAULT_GENERAL_OPTS,
    create_user,
    fetch_user_record,
    load_chart,
    save_chart,
)
from const import AI_Q, LANGS, ORBS, PDF_COLOR, ROW_HEIGHT, SESS, VAR
from datetime import date as Date
from natal import Chart, Data
from natal.config import Display, HouseSys
from natal.const import ASPECT_NAMES, PLANET_NAMES
from streamlit.column_config import DatetimeColumn, LinkColumn
from utils import (
    all_timezones,
    charts_df,
    cities_df,
    clear_input,
    data_db,
    i,
    pdf_html,
    pdf_io,
    scroll_to_bottom,
    stats_html,
    step,
    sync,
    update_orbs,
    validate_lat,
)


def segmented_ui():
    with st.container(key="chart_type_selector"):
        # st.subheader(i("chart_type"))
        SESS.chart_type = VAR.chart_type
        st.segmented_control(
            i("chart_type"),
            options=["birth_page", "synastry_page", "transit_page", "solar_return_page"],
            key="chart_type",
            width="stretch",
            format_func=lambda x: i(x),
            label_visibility="collapsed",
            on_change=lambda: clear_input() and update_orbs() and sync("chart_type"),
        )


def sidebar_ui():
    with st.sidebar:
        with st.expander(i("options"), expanded=True):
            labels = ["general", "orbs"]
            match VAR.chart_type:
                case "birth_page":
                    labels.append("birth")
                case "synastry_page":
                    labels += ["birth", "synastry"]
                case "transit_page":
                    labels += ["birth", "transit"]
                case "solar_return_page":
                    labels.append("solar_return_page")
            tabs = list(st.tabs([i(label) for label in labels]))
            with tabs[0]:
                general_opt()
            with tabs[1]:
                orb_opt()
            with tabs[2]:
                display_opt(1)
            if len(labels) > 3:
                with tabs[3]:
                    display_opt(2)

        if st.user.is_logged_in:
            saved_charts_ui()
            st.button(
                i("logout"),
                icon=":material/logout:",
                width="stretch",
                on_click=lambda: clear_input() and st.logout(),
            )
        else:
            st.button(i("login"), icon=":material/login:", width="stretch", on_click=st.login)


def general_opt():
    """general options from database, or show default options if user not logged in"""

    # print("general_opt start:", datetime.now())
    def update_db(key: str):
        sync(key)
        if st.user.is_logged_in:
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
        i("house_system"),
        options=HouseSys._member_names_,
        key="house_sys",
        format_func=i,
        on_change=lambda: validate_lat() and update_db("house_sys"),
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
        i("pdf_color"),
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

    def update_display(kind: str):
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
        i("inner_planets"),
        key=f"inner_display{id}",
        use_container_width=True,
        on_click=lambda: update_display("inner"),
    )
    c2.button(
        i("classic"),
        key=f"classic_display{id}",
        use_container_width=True,
        on_click=lambda: update_display("classic"),
    )
    c3.button(
        i("default"),
        key=f"default_display{id}",
        use_container_width=True,
        on_click=lambda: update_display("default"),
    )


def input_ui(id: int):
    """natal data input ui"""

    def set_lat_lon_dt_tz():
        """return lat, lon, utc datetime from a chart input ui"""
        city = f"city{id}"
        sync(city)
        # locate the row with the city name
        rows = cities_df()[cities_df()["city"] == VAR[city]]
        if rows.empty:
            return

        row = rows.iloc[0]
        for prop in ["lat", "lon", "tz"]:
            VAR[f"{prop}{id}"] = row[prop]

    def name_and_city():
        name_key = f"name{id}"
        name_container_key = f"name_container{id}"
        name_disabled = False

        if id == 2 and VAR.chart_type == "transit_page":
            name_container_key = f"transit_name{id}"
            VAR[name_key] = i("transit")
            name_disabled = True

        with st.container(key=f"name_and_city{id}", horizontal=True, horizontal_alignment="center"):
            with st.container(key=name_container_key):
                SESS[name_key] = VAR[name_key]
                st.text_input(
                    i("name"),
                    key=name_key,
                    disabled=name_disabled,
                    on_change=lambda: sync(name_key),
                )

            if id == 1 and SESS.chart_type == "solar_return_page":
                SESS["solar_return_year"] = VAR["solar_return_year"]
                st.number_input(
                    i("solar_return_year"),
                    key="solar_return_year",
                    min_value=1900,
                    max_value=2100,
                    step=1,
                    format="%i",
                    on_change=lambda: sync("solar_return_year"),
                )

            city_key = f"city{id}"
            city = VAR[city_key]
            SESS[city_key] = None if city == ("", "") else city
            st.selectbox(
                i("city"),
                options=cities_df(),
                key=city_key,
                placeholder=i("city_placeholder"),
                accept_new_options=True,
                help=i("city_help"),
                on_change=set_lat_lon_dt_tz,
            )

    def lat_lon_tz():
        c1, c2, c3 = st.columns(3)
        lat, lon, tz = f"lat{id}", f"lon{id}", f"tz{id}"

        SESS[lat] = VAR[lat]
        c1.number_input(
            i("latitude"),
            key=lat,
            min_value=-89.99,
            max_value=89.99,
            on_change=lambda: validate_lat() and sync(lat),
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

    def date_hr_min():
        with st.container(key=f"date-row{id}", horizontal=True):
            date_key = f"date{id}"
            SESS[date_key] = VAR[date_key]
            st.date_input(
                i("birth_date")
                if id == 1 or VAR.chart_type == "synastry_page"
                else i("transit_date"),
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
                help=i("daylight_saving_time"),
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

    name_and_city()
    lat_lon_tz()
    date_hr_min()


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

            def disable_save():
                lat_lon_tz = VAR.lat2 and VAR.lon2 and VAR.tz2
                match VAR.chart_type:
                    case "birth_page" | "solar_return_page":
                        return False
                    case "synastry_page":
                        return not (VAR.name2 and lat_lon_tz)
                    case "transit_page":
                        return not lat_lon_tz

            st.button(
                "",
                icon=":material/save:",
                key="save",
                on_click=lambda: st.toast(i("chart_created"), icon=":material/check:")
                if save_chart(st.user.email) == "create"
                else st.toast(i("chart_updated"), icon=":material/check:"),
                help=i("save_chart"),
                disabled=disable_save(),
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
                if st.button("", icon=":material/print:", key="pdf-button", help=i("gen_pdf")):
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
                        help=i("download_pdf"),
                    )


def chart_ui(data1: Data, data2: Data = None):
    st.write("")
    chart = Chart(data1=data1, data2=data2, width=VAR.chart_size)
    with st.container(key="chart_svg"):
        st.markdown(chart.svg, unsafe_allow_html=True)
    # reset chat history when loading new chart
    if "chat" in VAR:
        del VAR["chat"]


def stats_ui(data1: Data, data2: Data | None):
    with st.container(key="status_ui"):
        html = stats_html(data1, data2)
        st.markdown(html, unsafe_allow_html=True)


def ai_ui(data1: Data, data2: Data | None) -> None:
    st.write("")
    with st.expander(i("question_ideas"), expanded=True):
        with st.container(key="question_ideas_container", height=140, border=False):
            for questions in AI_Q[VAR.chart_type]:
                question = questions[VAR.lang_num]
                st.button(
                    question,
                    width="stretch",
                    type="tertiary",
                    icon=":material/arrow_right:",
                    on_click=SESS.update,
                    args=({"chat_input": question},),
                )

    # Initialize new chat only when new chart is loaded, this keeps the history during rerun
    if VAR.get("chat") is None:
        VAR["chat"] = new_chat(data1, data2)
    # Display chat history
    avatar = {"user": "👤", "assistant": "💫"}
    for message in VAR["chat"].messages[1:]:
        role = message["role"]
        text = message["content"]
        with st.chat_message(role, avatar=avatar[role]):
            st.markdown(text)

    def handle_user_input(prompt: str):
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

    # user input
    st.chat_input(
        i("chat_placeholder"),
        key="chat_input",
        on_submit=lambda: handle_user_input(SESS.chat_input),
    )


def saved_charts_ui():
    def on_select(data: pd.DataFrame):
        selected = SESS.saved_charts.selection.cells
        if selected:
            row = data.iloc[selected[0][0]]  # first value of first cell
            load_chart(row.to_dict())

    st.subheader(i("saved_charts"))
    data = charts_df()
    if data is None:
        st.info(i("no_saved_charts"))
    else:
        height = (len(data) + 1) * ROW_HEIGHT + 2
        column_config = {
            "name1": i("name"),
            "name2": i("synastry"),
            "city1": i("city"),
            "city2": i("city"),
            "age1": i("age"),
            "age2": i("age"),
            "dt2": DatetimeColumn(i("transit_date"), format="YYYY-MM-DD"),
            "solar_return_year": i("solar_return_year"),
            "delete": LinkColumn("", display_text=":material/delete:"),
        }

        column_order = ["name1", "city1", "age1"]
        match VAR.chart_type:
            case "synastry_page":
                column_order.extend(["name2", "city2", "age2"])
            case "transit_page":
                column_order.append("dt2")
            case "solar_return_page":
                column_order.append("solar_return_year")
        column_order.append("delete")

        st.dataframe(
            data,
            hide_index=True,
            height=height,
            column_config=column_config,
            column_order=column_order,
            row_height=ROW_HEIGHT,
            key="saved_charts",
            selection_mode="single-cell",
            on_select=lambda d=data: on_select(d),
        )
