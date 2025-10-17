import json
import streamlit as st
from const import DEFAULT_GENERAL_OPTS, VAR
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
    **{f"{prop}{i}": (str) for i in "12" for prop in ["name", "tz"]},
    **{f"city{i}": (str) for i in "12"},
    **{f"{prop}{i}": (float | None, None) for i in "12" for prop in ["lat", "lon"]},
    **{f"dt{i}": (datetime) for i in "12"},
    **{aspect: (int, 0) for aspect in ASPECT_NAMES},
    **{f"{body}{i}": (bool, False) for body in Display.model_fields for i in "12"},
)


class DataArchiveDict(DataArchive, Dictable): ...


def archive_str(var: DotDict = VAR) -> str:
    """Return a JSON string of the current chart data."""

    try:
        data = {f"{prop}{i}": var[f"{prop}{i}"] for prop in ["name", "city", "lat", "lon", "tz"] for i in "12"}
        data |= {f"dt{i}": get_dt(i) for i in [1, 2]}
        data |= {asp: var[asp] for asp in ASPECT_NAMES}
        data |= {f"{body}{i}": var[f"{body}{i}"] for body in Display.model_fields for i in "12"}
        model = DataArchive.model_validate(data)
    except ValidationError as e:
        st.error(e)
        return
    return model.model_dump_json()


def data_hash(var: DotDict = VAR) -> str:
    """hash the data to avoid inserting duplicate charts"""
    raw_data = {
        f"{prop}{i}": var[f"{prop}{i}"] for prop in ["name", "city", "lat", "lon", "tz", "hr", "min"] for i in "12"
    }
    raw_data |= {f"date{i}": var[f"date{i}"].strftime("%Y-%m-%d") for i in "12"}
    return md5(json.dumps(raw_data).encode()).hexdigest()


def load_chart(data: dict, var: DotDict = VAR):
    """Import chart data from a dictionary."""
    try:
        data = DataArchiveDict.model_validate(data)
    except ValidationError as e:
        st.error(e)
        return

    for i in "12":
        for prop in ["name", "city", "lat", "lon", "tz"]:
            var[f"{prop}{i}"] = data[f"{prop}{i}"]
        var[f"date{i}"] = data[f"dt{i}"].date()
        var[f"hr{i}"] = data[f"dt{i}"].hour
        var[f"min{i}"] = data[f"dt{i}"].minute

        for body in Display.model_fields:
            var[f"{body}{i}"] = data[f"{body}{i}"]

    for asp in ASPECT_NAMES:
        var[asp] = data[asp]


def save_chart(email: str) -> Literal["overwrite", "create"]:
    """Save a chart to the database. overwrite or create depending if hash exists"""
    hash = data_hash()
    cursor = data_db().cursor()
    data = archive_str()
    values = [data, hash]
    # print(data)
    if hash_exists(email, hash):
        sql = "UPDATE charts SET data = ? WHERE hash = ?"
        output = "overwrite"
    else:
        sql = "INSERT INTO charts (data, hash, email) VALUES (?, ?, ?)"
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
        (email, {", ".join(DEFAULT_GENERAL_OPTS)}) 
        VALUES (?, {", ".join(["?"] * len(DEFAULT_GENERAL_OPTS))});""",
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
    sql = f"SELECT {', '.join(DEFAULT_GENERAL_OPTS)} FROM users WHERE email = ?"
    cursor = data_db().cursor()
    cursor.execute(sql, (email,))
    saved_vals = cursor.fetchone()
    if saved_vals is None:
        return None
    return dict(zip(DEFAULT_GENERAL_OPTS, saved_vals))
