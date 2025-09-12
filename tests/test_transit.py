import json
from . import transit_sample
from archive import archive_str, import_data
from datetime import date
from io import BytesIO
from pytest import fixture
from streamlit.runtime.state.safe_session_state import SafeSessionState
from streamlit.testing.v1 import AppTest


@fixture(scope="package")
def transit():
    return AppTest.from_file("main.py", default_timeout=10000).run()


@fixture(scope="package")
def sess(transit: AppTest):
    return transit.session_state


def test_default_date(transit: AppTest):
    assert transit.date_input(key="date2").value == date.today()


def test_sample_data(transit: AppTest, sess: SafeSessionState):
    transit.text_input(key="name1").set_value("sample")
    transit.date_input(key="date1").set_value(date(1976, 4, 20))
    transit.selectbox(key="hr1").set_value(18)
    transit.selectbox(key="min1").set_value(58)
    transit.selectbox(key="city1").set_value("Hong Kong - HK")

    transit.date_input(key="date2").set_value(date(2014, 4, 20))
    transit.selectbox(key="hr2").set_value(18)
    transit.selectbox(key="min2").set_value(48)
    transit.selectbox(key="city2").set_value("Taipei - TW")

    transit.run()

    assert SESS["name1"] == "sample"
    assert SESS["city1"] == "Hong Kong - HK"
    assert SESS["date1"] == date(1976, 4, 20)
    assert SESS["hr1"] == 18
    assert SESS["min1"] == 58
    assert SESS["city2"] == "Taipei - TW"
    assert SESS["date2"] == date(2014, 4, 20)
    assert SESS["hr2"] == 18
    assert SESS["min2"] == 48


def test_change_orbs(transit: AppTest, sess: SafeSessionState):
    transit.button(key="transit_orbs").click().run()
    assert SESS.conjunction == 2
    assert SESS.opposition == 2
    assert SESS.trine == 2
    assert SESS.square == 2
    assert SESS.sextile == 1


def test_change_displays(transit: AppTest, sess: SafeSessionState):
    transit.button(key="inner_display2").click().run()
    assert SESS.sun2 == True
    assert SESS.moon2 == True
    assert SESS.mercury2 == True
    assert SESS.asc_node2 == False
    assert SESS.jupiter2 == False
    assert SESS.pluto2 == False


def test_save(sess: SafeSessionState, transit_sample: str):
    assert json.loads(archive_str(sess)) == json.loads(transit_sample)


def test_prev_button(transit: AppTest, sess: SafeSessionState):
    # press prev button
    transit.button(key="prev").click().run()
    assert SESS.date1 == date(1976, 4, 20)
    assert SESS.name2 == "transit"
    assert SESS.date2 == date(2014, 4, 19)


def test_import(sess: SafeSessionState, transit_sample: str):
    import_data(BytesIO(transit_sample.encode()), sess)
    assert json.loads(archive_str(sess)) == json.loads(transit_sample)
