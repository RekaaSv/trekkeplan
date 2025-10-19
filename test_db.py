import configparser

from db import queries
from db.connection import ConnectionManager

def test():
    config = configparser.ConfigParser()
    config.read("trekkeplan.cfg")
    db_config = config["mysql"]

    conn_mgr = ConnectionManager(db_config)

    queries.read_race(conn_mgr, 179)

test()
