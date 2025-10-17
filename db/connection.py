import configparser
import mysql.connector

from gui.main_window import MainWindow


def get_connection():
#    print("get_connection start")
    try:
        db_config = MainWindow.hent_mysql_config("trekkeplan.cfg")
        connection = mysql.connector.connect(**db_config)
#        print("get_connection slutt")
        return connection
    except Exception as e:
        print("Feil: {e}")
