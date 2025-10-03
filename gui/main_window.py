from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, \
    QHeaderView
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
        self.tableNotPlanned.setMinimumSize(300, 100)
        self.tableNotPlanned.setMaximumSize(300, 800)
        self.tableNotPlanned.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableNotPlanned.verticalHeader().setVisible(False)

        self.tableBlockLag = QTableWidget()
        self.tableBlockLag.setMinimumSize(120, 100)
        self.tableBlockLag.setMaximumSize(120, 800)
        self.tableBlockLag.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBlockLag.verticalHeader().setVisible(False)

        self.tableClassStart = QTableWidget()
        self.tableClassStart.setMinimumSize(800, 100)
        self.tableClassStart.setMaximumSize(800, 1200)
        self.tableClassStart.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableClassStart.verticalHeader().setVisible(False)

        self.moveButton = QPushButton("==>")
        self.moveButton.setFixedWidth(100)
        self.moveButton.setEnabled(False)  # deaktivert til å begynne med
        self.addBlockButton = QPushButton("+")
        self.drawButton = QPushButton("Trekk starttider")
        self.chk1Button = QPushButton("Klasser, løyper, post1")
        self.chk2Button = QPushButton("Sjekk samtidige")

        #        self.load_button.clicked.connect(self.load_data)

        rows1, columns1 = queries.read_not_planned(self.conn, self.raceId)
        rows2, columns2 = queries.read_block_lags(self.conn, self.raceId)
        rows3, columns3 = queries.read_class_starts(self.conn, self.raceId)

        self.populate_table(self.tableNotPlanned, columns1, rows1)
        self.populate_table(self.tableBlockLag, columns2, rows2)
        self.populate_table(self.tableClassStart, columns3, rows3)

        self.tableNotPlanned.setColumnHidden(0, True)
        self.tableNotPlanned.sortItems(1, order=Qt.AscendingOrder)
        self.tableNotPlanned.resizeColumnsToContents()
        self.tableNotPlanned.resizeRowsToContents()
        header = self.tableNotPlanned.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.tableBlockLag.setColumnHidden(0, True)
        self.tableBlockLag.setColumnHidden(1, True)
        self.tableBlockLag.sortItems(2, order=Qt.AscendingOrder)
        self.tableBlockLag.resizeColumnsToContents()
        self.tableBlockLag.resizeRowsToContents()
        header2 = self.tableBlockLag.horizontalHeader()
        header2.setSectionResizeMode(1, QHeaderView.Stretch)

        self.tableClassStart.setColumnHidden(0, True)
        self.tableClassStart.resizeColumnsToContents()
        self.tableClassStart.resizeRowsToContents()
        header3 = self.tableClassStart.horizontalHeader()
        header3.setSectionResizeMode(1, QHeaderView.Stretch)

        #
        # Layout
        #
        main_layout = QHBoxLayout()
        column1_layout = QVBoxLayout()
        column2_layout = QVBoxLayout()
        column3_layout = QVBoxLayout()
        column4_layout = QVBoxLayout()

        column1_layout.addWidget(title_non_planned)
        column1_layout.addWidget(self.tableNotPlanned)
        column1_layout.addStretch()
        column1_layout.addWidget(self.chk1Button)

        column2_layout.addSpacing(200)
        column2_layout.addWidget(self.moveButton)
        column2_layout.addStretch()

        #        layout.addWidget(self.status)

        column3_layout.addWidget(title_block_lag)
        column3_layout.addWidget(self.addBlockButton)
        column3_layout.addWidget(self.tableBlockLag)
        column3_layout.addStretch()

        column4_layout.addWidget(title_class_start)
        column4_layout.addWidget(self.tableClassStart)
        column4_layout.addStretch()
        column4_layout.addWidget(self.drawButton)
        column4_layout.addWidget(self.chk2Button)

        main_layout.addLayout(column1_layout)
        main_layout.addLayout(column2_layout)
        main_layout.addLayout(column3_layout)
        main_layout.addLayout(column4_layout)

        self.setLayout(main_layout)

    def populate_table(self, table, columns: list[any], rows):
        table.setColumnCount(len(columns))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(columns)

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = "" if value is None else QTableWidgetItem(str(value))
                if isinstance(value, (int, float)) or columns[col_idx] in ("Starttid", "Nestetid"):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row_idx, col_idx, QTableWidgetItem(item))
        table.setSortingEnabled(True)

#        self.status.setText("Status: Data lastet")

