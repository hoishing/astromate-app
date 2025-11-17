import json
import streamlit as st
from const import GENERAL_OPTS, SESS
from datetime import datetime
from hashlib import md5
from natal.config import Dictable, Display
from natal.const import ASPECT_NAMES
from natal.data import DotDict
from pydantic import ValidationError, create_model
from typing import Iterable, Literal
from utils import data_db, get_dt

DataArchive = create_model(
    "DataArchive",
    **{f"name{i}": (str) for i in "12"},
    **{f"{prop}{i}": (str | None, None) for i in "12" for prop in ["city", "tz"]},
    **{f"{prop}{i}": (float | None, None) for i in "12" for prop in ["lat", "lon"]},
    **{f"dt{i}": (datetime) for i in "12"},
    **{aspect: (int, 0) for aspect in ASPECT_NAMES},
    **{f"{body}{i}": (bool, False) for body in Display.model_fields for i in "12"},
    **{"solar_return_year": (int)},
)


class DataArchiveDict(DataArchive, Dictable): ...


def archive_str(sess: DotDict = SESS) -> str:
    """Return a JSON string of the current chart data."""

    try:
        data = {
            f"{prop}{i}": sess[f"{prop}{i}"]
            for prop in ["name", "city", "lat", "lon", "tz"]
            for i in "12"
        }
        data |= {f"dt{i}": get_dt(i) for i in [1, 2]}
        data |= {asp: sess[asp] for asp in ASPECT_NAMES}
        data |= {f"{body}{i}": sess[f"{body}{i}"] for body in Display.model_fields for i in "12"}
        data |= {"solar_return_year": sess["solar_return_year"]}
        model = DataArchive.model_validate(data)
    except ValidationError as e:
        st.error(e)
        return
    return model.model_dump_json()


def data_hash(sess: DotDict = SESS) -> str:
    """hash the data to avoid inserting duplicate charts"""
    raw_data = [
        sess[f"{prop}{i}"]
        for prop in ["name", "city", "lat", "lon", "tz", "hr", "min"]
        for i in "12"
    ]
    raw_data += [sess[f"date{i}"].strftime("%Y-%m-%d") if sess[f"date{i}"] else None for i in "12"]
    raw_data += [sess["chart_type"], sess["solar_return_year"]]
    return md5(json.dumps(raw_data).encode()).hexdigest()


def load_chart(data: dict, sess: DotDict = SESS):
    """Import chart data from a dictionary."""
    try:
        data = DataArchiveDict.model_validate(data)
    except ValidationError as e:
        st.error(e)
        return

    for i in "12":
        for prop in ["name", "city", "lat", "lon", "tz"]:
            sess[f"{prop}{i}"] = data[f"{prop}{i}"]
        sess[f"date{i}"] = data[f"dt{i}"].date()
        sess[f"hr{i}"] = data[f"dt{i}"].hour
        sess[f"min{i}"] = data[f"dt{i}"].minute

        for body in Display.model_fields:
            sess[f"{body}{i}"] = data[f"{body}{i}"]

    for asp in ASPECT_NAMES:
        sess[asp] = data[asp]

    sess["solar_return_year"] = data["solar_return_year"]


def save_chart(email: str) -> Literal["overwrite", "create"]:
    """Save a chart to the database. overwrite or create depending if hash exists"""
    hash = data_hash()
    cursor = data_db().cursor()
    data = archive_str()
    values = [data, hash, SESS.chart_type]
    # print(data)
    if hash_exists(email, hash):
        sql = "UPDATE charts SET data = ? WHERE hash = ? and chart_type = ?"
        output = "overwrite"
    else:
        sql = "INSERT INTO charts (data, hash, chart_type, email) VALUES (?, ?, ?, ?)"
        values.append(email)
        output = "create"
    cursor.execute(sql, values)
    data_db().commit()
    return output


def delete_chart(email: str, chart_hash: str) -> None:
    """Delete a chart by its hash."""
    sql = "DELETE FROM charts WHERE hash = ? AND email = ?"
    cursor = data_db().cursor()
    cursor.execute(sql, (chart_hash, email))
    data_db().commit()


def create_user(options: Iterable) -> None:
    cursor = data_db().cursor()
    cursor.execute(
        f"""INSERT INTO users 
        (email, {", ".join(GENERAL_OPTS)}) 
        VALUES (?, {", ".join(["?"] * len(GENERAL_OPTS))});""",
        options,
    )
    data_db().commit()


def hash_exists(email: str, hash: str) -> bool:
    """Check if a chart with the same hash and email exists"""
    sql = "SELECT 1 FROM charts WHERE email = ? AND hash = ?"
    cursor = data_db().cursor()
    cursor.execute(sql, (email, hash))
    return cursor.fetchone() is not None


def fetch_user_record(email: str) -> dict | None:
    sql = f"SELECT {', '.join(GENERAL_OPTS)} FROM users WHERE email = ?"
    cursor = data_db().cursor()
    cursor.execute(sql, (email,))
    saved_vals = cursor.fetchone()
    if saved_vals is None:
        return None
    return dict(zip(GENERAL_OPTS, saved_vals))
