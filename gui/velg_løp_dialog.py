from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import Qt

class SelectRaceDialog(QDialog):
    def __init__(self, løp_liste: list[tuple[int, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Velg et annet løp")
        self.resize(700, 300)

        self.valgt_løpsid = None

        layout = QVBoxLayout(self)

        # Tabell
        self.table_race = QTableWidget()
        self.table_race.setColumnCount(2)
        self.table_race.setHorizontalHeaderLabels(["Løpsnavn", "ID"])
        self.table_race.setRowCount(len(løp_liste))
        self.table_race.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_race.setSelectionMode(QTableWidget.SingleSelection)
        self.table_race.verticalHeader().setVisible(False)
        self.table_race.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        for rad, (løpsid, navn) in enumerate(løp_liste):
            self.table_race.setItem(rad, 0, QTableWidgetItem(navn))
            id_item = QTableWidgetItem(str(løpsid))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table_race.setItem(rad, 1, id_item)

        layout.addWidget(self.table_race)

        # Knapper
        knapp_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        avbryt_btn = QPushButton("Avbryt")
        knapp_layout.addWidget(ok_btn)
        knapp_layout.addWidget(avbryt_btn)
        layout.addLayout(knapp_layout)

        ok_btn.clicked.connect(self.ok_klikket)
        avbryt_btn.clicked.connect(self.reject)

    def ok_klikket(self):
        valgt = self.table_race.currentRow()
        if valgt >= 0:
            id_item = self.table_race.item(valgt, 3)
            self.valgt_løpsid = int(id_item.text())
            self.accept()