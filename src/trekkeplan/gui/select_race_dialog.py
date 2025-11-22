import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton
)
from PyQt5.QtCore import Qt

from trekkeplan.db import sql


class SelectRaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.info("SelectRaceDialog")
        self.parent = parent
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Velg et løp")
        self.resize(600, 300)
        self.setFont(parent.font())  # arver font fra hovedvinduet
        self.col_widths_races = [100, 400, 70, 0]

        logging.info("SelectRaceDialog 2")

        self.selected_race_id = None

        # Tabell
        self.table_race = QTableWidget()
        self.table_race.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_race.setSelectionMode(QTableWidget.SingleSelection)
        self.table_race.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_race.verticalHeader().setVisible(False)
        self.table_race.horizontalHeader().setStyleSheet(self.parent.table_header_style_sheet)
        self.table_race.setStyleSheet(self.parent.table_style_sheet)
#        parent.table_race.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        logging.info("SelectRaceDialog 3")

        # Knapper
        layout_buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(self.parent.button_style)
        cancel_btn = QPushButton("Avbryt")
        cancel_btn.setStyleSheet(self.parent.button_style)
        layout_buttons.addWidget(ok_btn)
        layout_buttons.addWidget(cancel_btn)

        ok_btn.clicked.connect(self.ok_clicked)
        cancel_btn.clicked.connect(self.reject)
        logging.info("SelectRaceDialog 4")

        layout = QVBoxLayout()
        layout.addWidget(self.table_race)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        logging.info("SelectRaceDialog.refresh")
        rows, columns = None, None
        rows, columns = sql.read_race_list(self.parent.conn_mgr)
        self.parent.populate_table(self.table_race, columns, rows)
        self.table_race.setColumnHidden(3, True)

        self.parent.set_table_sizes(self.table_race, self.col_widths_races)

    def ok_clicked(self):
        valgt = self.table_race.currentRow()
        if valgt >= 0:
            id_item = self.table_race.item(valgt, 3)
            self.selected_race_id = int(id_item.text())
            self.accept()