from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt

from db import queries


class SelectRaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent.log: print("SelectRaceDialog")
        self.parent = parent
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Velg et løp")
        self.resize(600, 300)
        self.setFont(parent.font())  # arver font fra hovedvinduet
        self.col_widths_races = [100, 400, 70, 0]

        if parent.log: print("SelectRaceDialog 2")

        self.valgt_løpsid = None

        # Tabell
        self.table_race = QTableWidget()
        self.table_race.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_race.setSelectionMode(QTableWidget.SingleSelection)
        self.table_race.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_race.verticalHeader().setVisible(False)
#        self.table_race.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        if parent.log: print("SelectRaceDialog 3")

        # Knapper
        knapp_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        avbryt_btn = QPushButton("Avbryt")
        knapp_layout.addWidget(ok_btn)
        knapp_layout.addWidget(avbryt_btn)

        ok_btn.clicked.connect(self.ok_klikket)
        avbryt_btn.clicked.connect(self.reject)
        if parent.log: print("SelectRaceDialog 4")

        layout = QVBoxLayout()
        layout.addWidget(self.table_race)
        layout.addLayout(knapp_layout)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        if self.parent.log: print("SelectRaceDialog.refresh")
        rows, columns = None, None
        rows, columns = queries.read_race_list(self.parent.conn_mgr)
        if self.parent.log: print("SelectRaceDialog.refresh columns", columns)
        self.parent.populate_table(self.table_race, columns, rows)
        self.table_race.setColumnHidden(3, True)

        self.parent.set_table_sizes(self.table_race, self.col_widths_races)

    def ok_klikket(self):
        valgt = self.table_race.currentRow()
        if valgt >= 0:
            id_item = self.table_race.item(valgt, 3)
            self.valgt_løpsid = int(id_item.text())
            self.accept()