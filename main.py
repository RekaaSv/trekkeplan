from db.connection import get_connection
from gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    conn = get_connection()
    app = QApplication(sys.argv)
    window = MainWindow(conn)
    window.show()

    conn.close()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()