import configparser
import os

from db.connection import ConnectionManager
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys

def main():
    app = QApplication(sys.argv)
    icon_path = resource_path("terning.ico")
    pdf_path = resource_path("hjelp.pdf")

    try:
        # Sikrer at det fungerer også når exe-filen startes fra annet sted.
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_path = os.path.join(base_dir, "trekkeplan.cfg")

        config = configparser.ConfigParser()
        config.read(config_path)
        db_config = config["mysql"]

        conn_mgr = ConnectionManager(db_config)
        conn_mgr.get_connection()
    except Exception as e:
        QMessageBox.critical(None, "Feil ved DB-kobling", f"Kunne ikke koble til databasen:\n{e}")
        sys.exit(1)

    # DB-kobling OK, fortsett.
    window = MainWindow(config, conn_mgr, icon_path, pdf_path)
    window.show()

    sys.exit(app.exec_())

def resource_path(relative_path):
    """Finner riktig bane til ressursen, uansett om det kjøres fra .py eller .exe"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)



if __name__ == "__main__":
    main()