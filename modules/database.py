# -*- coding: utf-8 -*-

import mysql.connector, os, time
from datetime import date
from contextlib import contextmanager

MYSQL_KEY = os.environ.get('MYSQL_LOCAL_KEY')


def Calc_Less_2Months_Date(today=date.today()):
    """
    This function calculate nextdate (after 2 month) from pre-defined or today date
    and output result as a string.
    :param today: date.today() - format
    :return: nextdate in datetime format
    """
    extra_days = 0  # default difference in amount of days in various months
    while True:
        try:
            if today.month == 11:
                nextdate = today.replace(year=today.year + 1, month=1)
                break
            elif today.month == 12:
                nextdate = today.replace(year=today.year + 1, month=2)
                break
            else:
                nextdate = today.replace(month=today.month + 2)
                break
        except ValueError:
            # If this error occurs than in calculated month less days than in pre-defined
            today = today.replace(day=today.day - 1)
            extra_days += 1
    # adjust nextdate by extra_days if neccessary
    if extra_days > 0:
        nextdate = nextdate.replace(month=nextdate.month + 1, day=extra_days)
    # auxiliary vars for testing purposes
    d1 = today.strftime("%Y-%m-%d")
    d2 = nextdate.strftime("%Y-%m-%d")
    return nextdate


@contextmanager
def open_database():
    """
    Context manager for working with DB
    :return: Cursor object
    """
    cnx = mysql.connector.connect(
        host="localhost",  # local
        # host="169.254.147.97", # remote
        user="root",
        password=MYSQL_KEY,
        database="arm_metrolog")
    cur = cnx.cursor()
    try:
        yield cur
    finally:
        cnx.close()


def Get_mte_status(cur, status):
    """
    Perform and execute mysql command (select by M&TE status), obtain the all response from DB
    # result = cur.fetchall()  # This method fetches all rows from the last executed statement
    # result = cur.fetchone() # This method return the first row of the result
    :param status: INT (0-OutOfCalibration; 1-Calibrated+Less2months; 2-InStorage)
    :return: all results of query to DB
    """
    cur.execute("""SELECT m.AssetNum, m.Model, m.SerialNum, m.DueCalibration, k.Certificate  
                    FROM mte_list AS m RIGHT JOIN mte_calibration as k  
                    ON k.AssetNum=m.AssetNum
                    WHERE k.DueCalibration=m.DueCalibration AND m.Status =""" + status)
    result = cur.fetchall()
    return result


def Get_mte_type(cur, model):
    """
    Perform and execute mysql command (select by M&TE type), obtain the all response from DB
    :param model: STR part of M&TE name
    :return: all results of query to DB
    """
    sql_cmd = """SELECT m.AssetNum, m.Model, m.SerialNum, l.Location, m.UserManual from mte_location AS l
                RIGHT JOIN mte_list AS m ON l.AssetNum=m.AssetNum WHERE m.Model LIKE '%""" + model + "%'" \
                "GROUP BY m.AssetNum"
    cur.execute(sql_cmd)
    result = cur.fetchall()
    return result


def time_track(func):
    # Decorator for tracking time of function performance
    def surrogate(*args, **kwargs):
        started_at = time.time()

        # call external function for performance testing
        result = func(*args, **kwargs)

        ended_at = time.time()
        elapsed = round(ended_at - started_at, 4)
        print(f'time expired {elapsed}')
        return result

    return surrogate


@time_track
def Show_tables(cur):
    # Decorated func which List all available tables in DB
    cur.execute("SHOW TABLES")
    result = cur.fetchall()
    return result


def Show_data(cur, table):
    # Show all data from selected table
    cur.execute("SELECT * FROM " + table)
    result = cur.fetchall()
    return result


def Init():
    """
    Connect to MySQL database
    :return: bool status of connection
    """
    global cnx
    cnx = mysql.connector.connect(
        host="localhost",  # local
        # host="169.254.147.97", # remote
        user="root",
        password=MYSQL_KEY,
        database="arm_metrolog")
    # Get a cursor
    global cur
    cur = cnx.cursor()
    return cnx.is_connected()


def Close():
    # Close connection
    cnx.close()
    return cnx.is_connected()


if __name__ == "__main__":
    # Testing purposes
    with open_database() as odb:
        print(Show_tables(odb))
        for x in Get_mte_type(odb, model="Calys"):
            print(x)
