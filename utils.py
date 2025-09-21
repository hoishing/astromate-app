import sqlite3
import streamlit as st
from const import BODIES, I18N, SESS
from datetime import datetime, timedelta
from natal import Config, Data, HouseSys
from typing import Literal
from zoneinfo import ZoneInfo


def i(key: str) -> str:
    return I18N[key][SESS.lang_num]


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
def db_conn() -> sqlite3.Connection:
    return sqlite3.connect("astrobro.db", check_same_thread=False)


@st.cache_data
def all_timezones() -> list[str]:
    """get all timezones from database"""
    cursor = db_conn().cursor()
    cursor.execute("SELECT timezone FROM timezone")
    return cursor.fetchall()


@st.cache_data
def all_cities() -> list[tuple[str, str]]:
    """get all cities name and country from database"""
    cursor = db_conn().cursor()
    cursor.execute("SELECT name, country FROM cities")
    return cursor.fetchall()


def set_lat_lon_dt_tz(id: int) -> dict:
    """return lat, lon, utc datetime from a chart input ui"""
    columns = "lat, lon, timezone"
    cursor = db_conn().cursor()
    cursor.execute(
        f"SELECT {columns} FROM cities WHERE name = ? and country = ?",
        SESS[f"city{id}"],
    )
    (lat, lon, timezone) = cursor.fetchone()
    SESS[f"lat{id}"] = lat
    SESS[f"lon{id}"] = lon
    SESS[f"tz{id}"] = timezone


def natal_data(id: int) -> Data:
    """return natal data from a chart input ui"""
    display = {body: SESS[f"{body}{id}"] for body in BODIES}

    return Data(
        name=SESS[f"name{id}"],
        lat=SESS[f"lat{id}"],
        lon=SESS[f"lon{id}"],
        utc_dt=utc_of(id),
        moshier=True,
        config=Config(
            house_sys=HouseSys[SESS.house_sys],
            theme_type=SESS.theme_type,
            orb=SESS.orb,
            display=display,
        ),
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
