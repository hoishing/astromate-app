import pandas as pd
import streamlit as st
from ai import AI
from archive import (
    create_user,
    data_hash,
    fetch_user_record,
    load_chart,
    save_chart,
)
from const import DISPLAY, GENERAL_OPTS, MAX_CHART_SIZE, ORBS, PDF_COLOR, ROW_HEIGHT, SESS, SYMBOLS
from datetime import date as Date
from natal import Chart, Data
from natal.config import HouseSys
from natal.const import ASPECT_NAMES, PLANET_NAMES
from streamlit.column_config import DatetimeColumn, LinkColumn
from utils import (
    all_timezones,
    charts_df,
    cities_df,
    data_db,
    debug_print,
    i,
    pdf_html,
    pdf_io,
    reset_inputs,
    screenwidth_detector,
    stats_html,
    step,
    update_orbs,
)


def segmented_ui():
    def handle_change():
        if SESS.chart_type is None:
            SESS.chart_type = SESS.selected_chart_type
        else:
            SESS.selected_chart_type = SESS.chart_type
            update_orbs()
        reset_inputs()

    with st.container(key="chart_type_selector"):
        st.segmented_control(
            i("chart_type"),
            options=["birth_page", "synastry_page", "transit_page", "solar_return_page"],
            key="chart_type",
            width="stretch",
            format_func=lambda x: i(x),
            label_visibility="collapsed",
            on_change=handle_change,
        )


def sidebar_ui():
    # debug_print()
    with st.sidebar:
        with st.expander(i("options"), expanded=True):
            labels = ["general", "orbs"]
            match SESS.chart_type:
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
                on_click=st.logout,
            )
        else:
            st.button(i("login"), icon=":material/login:", width="stretch", on_click=st.login)


def general_opt():
    """general options from database, or show default options if user not logged in"""

    # print("general_opt start:", datetime.now())
    def update_db(key: str):
        if st.user.is_logged_in:
            sql = f"UPDATE users SET {key} = ? WHERE email = ?"
            cursor = data_db().cursor()
            cursor.execute(sql, (SESS[key], st.user.email))
            data_db().commit()

    if st.user.is_logged_in:
        # get user options from db
        if user_record := fetch_user_record(st.user.email):
            # user found, set general options from db
            for field in GENERAL_OPTS:
                SESS[field] = user_record[field]
        else:
            # create user with default options
            create_user([st.user.email] + [SESS[field] for field in GENERAL_OPTS])

    st.selectbox(
        i("house_system"),
        options=HouseSys._member_names_,
        key="house_sys",
        format_func=i,
        on_change=lambda: update_db("house_sys"),
    )

    c1, c2, c3 = st.columns(3)

    c1.segmented_control(
        i("pdf_color"),
        options=PDF_COLOR,
        key="pdf_color",
        width="stretch",
        format_func=lambda x: PDF_COLOR[x],
        on_change=lambda: update_db("pdf_color"),
    )

    c2.segmented_control(
        i("statistics"),
        options=[True, False],
        key="show_stats",
        width="stretch",
        format_func=lambda x: ":material/check: " if x else ":material/close:",
        on_change=lambda: update_db("show_stats"),
    )

    c3.segmented_control(
        "AI",
        options=[True, False],
        key="enable_ai",
        width="stretch",
        format_func=lambda x: ":material/check: " if x else ":material/close:",
        on_change=lambda: update_db("enable_ai"),
    )


def orb_opt():
    """orb settings"""

    def orb_input(aspect: str):
        SESS[aspect] = SESS[aspect]
        st.number_input(
            label=i(aspect),
            min_value=0,
            max_value=10,
            key=aspect,
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
        on_click=lambda: SESS.update(dict(zip(ASPECT_NAMES, [2, 2, 2, 2, 1, 0]))),
    )
    c2.button(
        i("default"),
        key="default_orbs",
        use_container_width=True,
        on_click=lambda: SESS.update(ORBS),
    )


def display_opt(id: int):
    """options for displaying a celestial body or not"""

    def update_display(kind: str):
        presets = {
            "inner": PLANET_NAMES[:5],
            "classic": PLANET_NAMES[:7],
            "default": PLANET_NAMES + ["north_node"],
        }
        planets = presets[kind] + ["asc"]
        data = dict.fromkeys(DISPLAY, False) | dict.fromkeys(planets, True)
        for body in data:
            SESS[f"{body}{id}"] = data[body]

    def toggle(body: str):
        key = f"{body}{id}"
        # prevent sess clean up if widget is not drawn on screen
        SESS[key] = SESS[key]
        st.toggle(SYMBOLS[body], key=key)

    with st.container(key=f"display_opt{id}"):
        c1, c2, c3 = st.columns(3)
        bodies = list(DISPLAY)
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

    def name():
        name_num = f"name{id}"
        name_container_key = f"name_container{id}"
        name_disabled = False

        if id == 2 and SESS.chart_type == "transit_page":
            name_container_key = f"transit_name{id}"
            SESS[name_num] = i("transit")
            name_disabled = True
        else:
            SESS[name_num] = SESS[name_num]  # prevent sess clean up

        with st.container(key=name_container_key):
            st.text_input(
                i("name"),
                key=name_num,
                disabled=name_disabled,
            )

    def solar_return_year():
        if id == 1 and SESS.chart_type == "solar_return_page":
            # prevent sess clean up if widget is not drawn on screen
            SESS.solar_return_year = SESS.solar_return_year
            st.number_input(
                label=i("solar_return_year"),
                key="solar_return_year",
                min_value=1900,
                max_value=2100,
                step=1,
                format="%i",
            )

    def city():
        city_num = f"city{id}"
        df = cities_df()

        def set_lat_lon_tz():
            """set lat, lon, tz from a city index"""
            if SESS.get(city_num) is None:
                return
            idx = df.index[df["city"] == SESS[city_num]][0]
            columns = ["lat", "lon", "tz"]
            row = df.iloc[idx][columns]
            for prop in columns:
                SESS[f"{prop}{id}"] = row[prop]

        SESS[city_num] = SESS[city_num]  # prevent sess clean up
        st.selectbox(
            i("city"),
            options=df["city"],
            key=city_num,
            placeholder=i("city_placeholder"),
            accept_new_options=True,
            help=i("city_help"),
            on_change=set_lat_lon_tz,
        )

    def lat_lon_tz():
        c1, c2, c3 = st.columns(3)
        lat, lon, tz = f"lat{id}", f"lon{id}", f"tz{id}"
        for key in [lat, lon, tz]:
            # prevent sess clean up if widget is not drawn on screen
            SESS[key] = SESS[key]

        max_lat = 66.5 if SESS.house_sys in ["Placidus", "Koch"] else 89.99
        try:
            c1.number_input(
                i("latitude"),
                key=lat,
                min_value=-max_lat,
                max_value=max_lat,
            )
        except Exception:
            st.error(i(SESS.house_sys) + i("latitude_error"))
            st.stop()

        c2.number_input(
            i("longitude"),
            key=lon,
            min_value=-179.99,
            max_value=179.99,
        )

        c3.selectbox(
            i("timezone"),
            all_timezones(),
            key=tz,
            placeholder=i("timezone_placeholder"),
        )

    def date_hr_min():
        date_key, hr_key, min_key = f"date{id}", f"hr{id}", f"min{id}"
        # prevent sess clean up if widget is not drawn on screen
        SESS[date_key] = SESS[date_key]
        SESS[hr_key] = SESS[hr_key]
        SESS[min_key] = SESS[min_key]

        with st.container(key=f"date-row{id}", horizontal=True):
            st.date_input(
                i("birth_date")
                if id == 1 or SESS.chart_type == "synastry_page"
                else i("transit_date"),
                max_value=Date(2300, 1, 1),
                min_value=Date(1800, 1, 1),
                format="YYYY-MM-DD",
                key=date_key,
            )

            st.selectbox(
                i("hour"),
                range(24),
                key=hr_key,
                help=i("daylight_saving_time"),
            )

            st.selectbox(
                i("minute"),
                range(60),
                key=min_key,
            )

    solar_return_year()
    with st.container(key=f"name_and_city{id}", horizontal=True):
        name()
        city()
    lat_lon_tz()
    date_hr_min()


def utils_ui(data1: Data, data2: Data | None):
    chart_id = 2 if data2 else 1
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
            on_click=lambda: step(chart_id, -1),
            key="prev",
            help=i("prev") + i(SESS.stepper_unit),
        )
        # prevent sess clean up if widget is not drawn on screen
        SESS.stepper_unit = SESS.stepper_unit
        st.selectbox(
            i("adjustment"),
            stepper_options,
            label_visibility="collapsed",
            format_func=lambda x: i(x),
            key="stepper_unit",
            width=90,
        )

        st.button(
            "",
            icon=":material/arrow_right:",
            on_click=lambda: step(chart_id, 1),
            key="next",
            help=i("next") + i(SESS.stepper_unit),
        )

        if st.user.is_logged_in:

            def disable_save():
                lat_lon_tz = SESS.lat2 and SESS.lon2 and SESS.tz2
                match SESS.chart_type:
                    case "birth_page" | "solar_return_page":
                        return False
                    case "synastry_page":
                        return not (SESS.name2 and lat_lon_tz)
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
                    name_parts = [SESS.name1]
                    if SESS.name2 and SESS.chart_type == "synastry_page":
                        name_parts.append(SESS.name2)
                    name_parts.append(i(SESS.chart_type))
                    filename = "_".join(name_parts)
                    st.download_button(
                        "",
                        icon=":material/download:",
                        data=pdf,
                        file_name=f"{filename}.pdf",
                        mime="application/pdf",
                        help=i("download_pdf"),
                    )


def stats_ui(data1: Data, data2: Data | None):
    if not SESS.show_stats:
        return
    with st.container(key="stats_ui"):
        html = stats_html(data1, data2)
        st.markdown(html, unsafe_allow_html=True)


def chart_ui(data1: Data, data2: Data = None):
    def update_chart_size():
        # print("screen width changed:", SESS.screen_detector["width"])
        SESS.chart_size = min(SESS.screen_detector["width"] + 48, MAX_CHART_SIZE)

    st.write("")
    screenwidth_detector(
        data=MAX_CHART_SIZE,
        key="screen_detector",
        isolate_styles=False,
        on_width_change=update_chart_size,
    )
    chart = Chart(data1=data1, data2=data2, width=SESS.chart_size)
    with st.container(key="chart_svg"):
        st.markdown(chart.svg, unsafe_allow_html=True)
    # check if chart data has changed
    if SESS["data_hash"] != data_hash():
        SESS["data_hash"] = data_hash()
        # reset chat history and ai questions
        SESS.ai = None


def ai_ui(data1: Data, data2: Data | None) -> None:
    if not SESS.enable_ai:
        return
    if SESS.ai is None:
        SESS.ai = AI(data1, data2)
    # st.code(ai.sys_prompt, language="markdown")
    SESS.ai.ui()


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
        match SESS.chart_type:
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
