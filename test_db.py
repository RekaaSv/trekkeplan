from db import queries
from db.connection import ConnectionManager

def test():
    conn_mgr = ConnectionManager.validate_config("trekkeplan.cfg")
    if conn_mgr:
        print("✅ Klar til bruk:", conn_mgr)
        conn = conn_mgr.get_connection()
        print("conn:", conn)
    else:
        print("❌ Feil i config eller tilkobling")

    queries.read_race(conn_mgr, 179)

test()
