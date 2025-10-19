import configparser
import os

from db.connection import ConnectionManager
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    # Sikrer at det fungerer også når exe-filen startes fra annet sted.
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(base_dir, "trekkeplan.cfg")

    config = configparser.ConfigParser()
    config.read(config_path)
    db_config = config["mysql"]

    conn_mgr = ConnectionManager(db_config)

    app = QApplication(sys.argv)

    window = MainWindow(config, conn_mgr)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()