from datetime import date
import pytest, os
from modules import database as db

MYSQL_KEY = os.environ.get('MYSQL_LOCAL_KEY')

"""
This module contains unit tests for database module's functions.
"""

# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Calc_Less_2Months_Date() with set of input parameters
# ----------------------------------------------------------------------------------------------------------------------
dates = [
    (2021, 1, 1, '2021-03-01'),
    (2021, 5, 31, '2021-07-31'),
    (2021, 6, 30, '2021-08-30'),
    (2021, 11, 30, '2022-01-30'),
    (2021, 12, 31, '2022-03-03')
]


@pytest.mark.parametrize('year, month, day, result', dates)
def test_Calc_Less_2Months_Date(year, month, day, result):
    test_date = date(year, month, day)
    assert db.Calc_Less_2Months_Date(test_date).strftime("%Y-%m-%d") == result


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Init() validate generated object and connection status
# ----------------------------------------------------------------------------------------------------------------------
def test_Init_Object():
    # General Pre-Condition for calling database module's functions
    ConStatus = db.Init()
    # assert str(type(db.cur)) == "<class 'mysql.connector.cursor.MySQLCursor'>"
    assert ConStatus


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Close() validate connection status after function's call
# ----------------------------------------------------------------------------------------------------------------------
def test_Close_Connection_Status():
    # General Post-Condition for calling database module's functions
    ConStatus = db.Close()
    assert ConStatus == False


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Show_data() with set of input parameters
# ----------------------------------------------------------------------------------------------------------------------
indices = [
    (0, 0, 1),
    (0, 1, 'HMP4040'),
    (1, 0, 2),
    (1, 1, 'APS-9501'),
]


@pytest.mark.parametrize('i, j, result', indices)
def test_Show_data(i, j, result):
    db.Init()
    answer = db.Show_data(db.cur, 'mte_list')
    db.Close()
    # answer = db.Show_data('mte_list')
    assert answer[i][j] == result


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Get_mte_status() with status == Calibrated
# ----------------------------------------------------------------------------------------------------------------------
def test_Get_mte_status():
    db.Init()
    answer = db.Get_mte_status(db.cur, status='1')
    db.Close()
    assert len(answer) != 0


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Get_mte_type() with set of input parameters
# ----------------------------------------------------------------------------------------------------------------------
types = [
    ('289'),
    ('Calys'),
    ('500/100'),
    ('APS'),
    ('HMP'),
    ('P4831')
]


@pytest.mark.parametrize('model', types)
def test_Get_mte_type(model):
    db.Init()
    answer = db.Get_mte_type(db.cur, model)
    db.Close()
    assert len(answer) != 0


# ----------------------------------------------------------------------------------------------------------------------
# TestCase for Show_tables() display list of available ttables in the DB
# ----------------------------------------------------------------------------------------------------------------------
def test_Show_tables():
    answer = [('mte_calibration',), ('mte_list',), ('mte_location',), ('mte_specification',),
              ('responsible_persons',), ('service_providers',), ('service_records',)]
    db.Init()
    assert db.Show_tables(db.cur) == answer
    db.Close()
