import configparser

from db.connection import ConnectionManager
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    config = configparser.ConfigParser()
    config.read("trekkeplan.cfg")
    db_config = config["mysql"]

    conn_mgr = ConnectionManager(db_config)

    app = QApplication(sys.argv)

    window = MainWindow(config, conn_mgr)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()