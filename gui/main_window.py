from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from db import queries
from db.connection import get_connection

class MainWindow(QWidget):
    def __init__(self, conn, raceid):
        super().__init__()
        self.conn = conn # Lagre connection.
        self.raceId = raceid

        self.setWindowTitle("Trekkeplan")
        self.setGeometry(0, 0, 1800, 900)

        #
        # Komponenter
        #
#        self.status = QLabel("Status: Ikke tilkoblet")
        style_table_header = "font-weight: bold; font-size: 16px; margin: 10px 0;"
        title_non_planned = QLabel("Ikke-planlagte klasser")
        title_non_planned.setStyleSheet(style_table_header)
        title_block_lag = QLabel("Bås/tidsslep")
        title_block_lag.setStyleSheet(style_table_header)
        title_class_start = QLabel("Klassevis starttider")
        title_class_start.setStyleSheet(style_table_header)

        self.tableNotPlanned = QTableWidget()
        self.tableNotPlanned.setEditTriggers(QTableWidget.NoEditTriggers)

        self.tableBlockLag = QTableWidget()
        self.tableClassStart = QTableWidget()

        self.moveButton = QPushButton("Flytt")
        self.addBlockButton = QPushButton("+")
        self.drawButton = QPushButton("Trekk starttider")
        self.chk1Button = QPushButton("Klasser, løyper, post1")
        self.chk2Button = QPushButton("Sjekk samtidige")
        #        self.load_button.clicked.connect(self.load_data)

        main_layout = QHBoxLayout()
        column1_layout = QVBoxLayout()
        column2_layout = QVBoxLayout()
        column3_layout = QVBoxLayout()
        column4_layout = QVBoxLayout()
        main_layout.addLayout(column1_layout)
        main_layout.addLayout(column2_layout)
        main_layout.addLayout(column3_layout)
        main_layout.addLayout(column4_layout)

        column1_layout.addWidget(title_non_planned)
        column1_layout.addWidget(self.tableNotPlanned)
        column1_layout.addWidget(self.chk1Button)

        column2_layout.addWidget(self.moveButton)
#        layout.addWidget(self.status)

        column3_layout.addWidget(title_block_lag)
        column3_layout.addWidget(self.addBlockButton)
        column3_layout.addWidget(self.tableBlockLag)

        column4_layout.addWidget(title_class_start)
        column4_layout.addWidget(self.tableClassStart)
        column4_layout.addWidget(self.drawButton)
        column4_layout.addWidget(self.chk2Button)

        self.setLayout(main_layout)

        rows, columns = queries.readNotPlanned(self.conn, self.raceId)

        self.tableNotPlanned.setColumnCount(len(columns))
        self.tableNotPlanned.setRowCount(len(rows))
        self.tableNotPlanned.setHorizontalHeaderLabels(columns)
        self.tableNotPlanned.setColumnHidden(0, True)

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                self.tableNotPlanned.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        self.tableNotPlanned.sortItems(1, order=Qt.AscendingOrder)
        self.tableNotPlanned.setSortingEnabled(True)

#        self.status.setText("Status: Data lastet")

