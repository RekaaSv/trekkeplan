import configparser
import logging
import os
import traceback

import pymysql

from db.connection import ConnectionManager
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys

def global_exception_hook(exctype, value, tb):
    logging.error("Uventet feil", exc_info=(exctype, value, tb))
    msg = f"{exctype.__name__}: {value}"
    QMessageBox.critical(None, "Uventet feil", msg)
    traceback.print_exception(exctype, value, tb)

def main():
    # Global feilhåndtering
    sys.excepthook = global_exception_hook

    # Start GUI
    app = QApplication(sys.argv)
    try:

        icon_path = resource_path("terning.ico")
        pdf_path = resource_path("hjelp.pdf")

        app.setStyleSheet("""
        QToolTip {
            background-color: rgb(255, 255, 220);  /* svak gul */
            color: black;
            border: 1px solid gray;
            padding: 4px;
            font-size: 10pt;
        }
        """)

        # Sikrer at det fungerer også når exe-filen startes fra annet sted.
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_path = os.path.join(base_dir, "trekkeplan.cfg")
        config = configparser.ConfigParser()
        config.read(config_path)
        db_config = config["mysql"]
        log_config = config["logging"]

        # Logging-oppsett ufra konfig fil.
        log_level = log_config.get("level", fallback="INFO")
        log_file = log_config.get("file", fallback="trekkeplan.log")
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

        conn_mgr = ConnectionManager(db_config)
        conn_mgr.get_connection()


        # DB-kobling OK, fortsett.
        window = MainWindow(config, conn_mgr, icon_path, pdf_path)
        window.show()
        sys.exit(app.exec_())
    except pymysql.Error as e:
        QMessageBox.critical(None, "Feil ved DB-kobling", f"Kunne ikke koble til databasen:\n{e}")
        traceback.print_exc()
        raise
    except Exception as e:
        logging.error("Systemfeil", exc_info=True)
        QMessageBox.critical(None, "Systemfeil", str(e))
        raise  # sender videre til global_exception_hook


def resource_path(relative_path):
    """Finner riktig bane til ressursen, uansett om det kjøres fra .py eller .exe"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    main()