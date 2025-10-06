import json
import streamlit as st
from const import ORBS
from datetime import datetime
from hashlib import md5
from io import BytesIO
from natal.config import Display, Orb
from pydantic import BaseModel
from streamlit.runtime.state.safe_session_state import SafeSessionState
from utils import data_db, get_dt


class DataArchive(BaseModel):
    name1: str
    city1: tuple[str, str] | None = None
    lat1: float
    lon1: float
    tz1: str
    dt1: datetime
    name2: str | None = None
    city2: tuple[str, str] | None = None
    lat2: float | None = None
    lon2: float | None = None
    tz2: str | None = None
    dt2: datetime | None = None
    house_sys: str
    theme_type: str
    orb: Orb
    display1: Display
    display2: Display


def archive_str(sess: SafeSessionState = st.session_state) -> str:
    """Return a JSON string of the current chart data."""
    return DataArchive(
        name1=sess.name1,
        city1=sess.city1,
        lat1=sess.lat1,
        lon1=sess.lon1,
        tz1=sess.tz1,
        dt1=get_dt(1),
        name2=sess.name2,
        city2=sess.city2,
        lat2=sess.lat2,
        lon2=sess.lon2,
        tz2=sess.tz2,
        dt2=get_dt(2) if (sess.name2 and sess.city2) else None,
        house_sys=sess.house_sys,
        theme_type=sess.theme_type,
        orb=Orb(**{asp: sess[asp] for asp in ORBS}),
        display1=sess.display1,
        display2=sess.display2,
    ).model_dump_json()


def data_hash(sess: SafeSessionState = st.session_state) -> str:
    """hash the data to avoid inserting duplicate charts"""
    raw_data = dict(
        name1=sess.name1,
        city1=sess.city1,
        lat1=sess.lat1,
        lon1=sess.lon1,
        tz1=sess.tz1,
        date1=sess.date1.strftime("%Y-%m-%d"),
        hr1=sess.hr1,
        min1=sess.min1,
        name2=sess.name2,
        city2=sess.city2,
        lat2=sess.lat2,
        lon2=sess.lon2,
        tz2=sess.tz2,
        date2=sess.date2.strftime("%Y-%m-%d"),
        hr2=sess.hr2,
        min2=sess.min2,
    )
    return md5(json.dumps(raw_data).encode()).hexdigest()


def import_data(fp: BytesIO | None, sess: SafeSessionState = st.session_state):
    """Import chart data from a JSON file."""
    if not fp:
        return
    data = DataArchive.model_validate_json(fp.read())
    sess.name1 = data.name1
    sess.city1 = data.city1
    sess.lat1 = data.lat1
    sess.lon1 = data.lon1
    sess.tz1 = data.tz1
    sess.date1 = data.dt1.date()
    sess.hr1 = data.dt1.hour
    sess.min1 = data.dt1.minute
    sess.name2 = data.name2
    sess.city2 = data.city2
    sess.lat2 = data.lat2
    sess.lon2 = data.lon2
    sess.tz2 = data.tz2
    sess.date2 = data.dt2.date() if data.dt2 else None
    sess.hr2 = data.dt2.hour if data.dt2 else 0
    sess.min2 = data.dt2.minute if data.dt2 else 0
    sess.house_sys = data.house_sys
    sess.theme_type = data.theme_type
    sess.display1 = data.display1
    sess.display2 = data.display2
    sess.orb = data.orb


def save_chart() -> None:
    sql = """
    INSERT INTO charts (hash, email, data) 
    VALUES (?, ?, ?)
    ON CONFLICT(hash) 
    DO UPDATE SET 
    email = excluded.email,
    data = excluded.data;
    """
    cursor = data_db().cursor()
    cursor.execute(sql, (data_hash(), st.user.email, archive_str()))
    data_db().commit()



def delete_chart(chart_hash: str) -> None:
    """Delete a chart by its hash."""
    sql = "DELETE FROM charts WHERE hash = ? AND email = ?"
    cursor = data_db().cursor()
    cursor.execute(sql, (chart_hash, st.user.email))
    data_db().commit()

