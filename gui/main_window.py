from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem
from db.connection import get_connection

class MainWindow(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn # Lagre connection.

        self.setWindowTitle("Trekkeplan")
        self.setGeometry(100, 100, 800, 600)

        self.status = QLabel("Status: Ikke tilkoblet")
        self.table1 = QTableWidget()
        self.load_button = QPushButton("Last data fra MySQL")
#        self.load_button.clicked.connect(self.load_data)
        self.load_data()

#        self.table1.setColumnCount(4)
#        self.table1.setRowCount(7)

        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(self.table1)
        layout.addWidget(self.load_button)

        self.setLayout(layout)

#        conn.close()

    def load_data(self):
        try:
            print("Prøver connection")
#            conn = get_connection()
            print("Tilkobling OK")
            cursor = self.conn.cursor()

#            classesNotInPlanSql = ""
#            """
            cursor.execute("SELECT * FROM races where id > 140 and id < 183")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            self.table1.setColumnCount(len(columns))
            self.table1.setRowCount(len(rows))
            self.table1.setHorizontalHeaderLabels(columns)
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    self.table1.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            self.status.setText("Status: Tilkoblet og data lastet")
        except Exception as e:
            print(f"Feil: {e}")
            self.status.setText(f"Feil: {e}")

