import sqlite3
import streamlit as st
from const import BODIES, SESS
from datetime import datetime, timedelta
from natal import Config, Data, HouseSys
from typing import Literal
from zoneinfo import ZoneInfo


def utc_of(dt: datetime, timezone: str) -> datetime:
    """convert local datetime to utc datetime

    args:
        dt: local datetime
        timezone: timezone string
    returns:
        utc datetime
    """
    local_tz = ZoneInfo(timezone)
    local_dt = dt.replace(tzinfo=local_tz)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt


def get_dt(id: int) -> datetime:
    """get datetime from session state"""
    date = SESS[f"date{id}"]
    hr = SESS[f"hr{id}"]
    minute = SESS[f"min{id}"]
    return datetime(date.year, date.month, date.day, hr, minute)


@st.cache_resource
def db_conn() -> sqlite3.Connection:
    return sqlite3.connect("astrobro.db")


@st.cache_data
def all_cities() -> list[tuple[str, str]]:
    """get all cities name and country from database"""
    cursor = db_conn().cursor()
    cursor.execute("SELECT name, country FROM cities")
    rows = cursor.fetchall()
    return rows


def lat_lon_dt(chart_id: int) -> dict:
    """return lat, lon, utc datetime from a chart input ui"""
    columns = "lat, lon, timezone"
    cursor = db_conn().cursor()
    cursor.execute(
        f"SELECT {columns} FROM cities WHERE name = ? and country = ?",
        SESS[f"city{chart_id}"],
    )
    (lat, lon, timezone) = cursor.fetchone()
    utc_dt = utc_of(get_dt(chart_id), timezone)
    return dict(lat=lat, lon=lon, utc_dt=utc_dt)


def natal_data(chart_id: int) -> Data:
    """return natal data from a chart input ui"""
    house_sys = HouseSys[SESS["house_sys"]]
    display = {body: SESS[f"{body}{chart_id}"] for body in BODIES}

    return Data(
        name=SESS[f"name{chart_id}"],
        **lat_lon_dt(chart_id),
        config=Config(
            house_sys=house_sys,
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
