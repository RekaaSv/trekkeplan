import configparser

from db.connection import ConnectionManager
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    conn_mgr = ConnectionManager.validate_config("trekkeplan.cfg")
    config = None
    if conn_mgr:
        print("✅ Klar til bruk:", conn_mgr)
        conn = conn_mgr.get_connection()
        config = conn_mgr.config
        print("conn:", conn)
    else:
        print("❌ Feil i config eller tilkobling")

    app = QApplication(sys.argv)

    window = MainWindow(config, conn_mgr)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()