from PyQt5.QtWidgets import QDialog, QTableWidget, QHBoxLayout, QTableWidgetItem

from db import queries


class SplitClubMates(QDialog):
    def __init__(self, rows, columns, klasse_data_func, parent=None):
        super().__init__(parent)
        if parent.log: print("SplitClubMates")
        self.parent = parent
        self.setWindowTitle("SplitClubMates")
        self.resize(1500, 700)

        self.venstre = QTableWidget()
        self.hoyre = QTableWidget()

        self.venstre.setSelectionBehavior(QTableWidget.SelectRows)
        self.venstre.setSelectionMode(QTableWidget.SingleSelection)
        self.venstre.verticalHeader().setVisible(False)

        self.hoyre.setSelectionBehavior(QTableWidget.SelectRows)
        self.hoyre.setSelectionMode(QTableWidget.MultiSelection)
        self.hoyre.verticalHeader().setVisible(False)

        if parent.log: print("SplitClubMates")
        parent.populate_table(self.venstre, columns, rows)
#        self._populate_venstre(problem_liste)
        self.venstre.itemSelectionChanged.connect(self._oppdater_hoyre)

        layout = QHBoxLayout()
        layout.addWidget(self.venstre)
        layout.addWidget(self.hoyre)
        self.setLayout(layout)
        if parent.log: print("SplitClubMates layout end")

#        self.klasse_data_func = klasse_data_func  # funksjon som henter klassevis data

    def _populate_venstre(self, data):
        self.venstre.setRowCount(len(data))
        self.venstre.setColumnCount(len(data[0]))
        self.venstre.setHorizontalHeaderLabels(["Navn", "Klubb", "Klasse", "Starttid"])
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.venstre.setItem(r, c, QTableWidgetItem(str(val)))

    def _oppdater_hoyre(self):
        if self.parent.log: print("_oppdater_hoyre")
        selected = self.venstre.currentRow()
        classid = self.venstre.item(selected, 1).text()
        if self.parent.log: print("_oppdater_hoyre", classid)

        rows, columns = queries.read_names(self.parent.conn_mgr, classid)
        self.parent.populate_table(self.hoyre, columns, rows)

"""
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.hoyre.setItem(r, c, QTableWidgetItem(str(val)))
            if row[0] == navn:
                self.hoyre.selectRow(r)
                self.hoyre.scrollToItem(self.hoyre.item(r, 0))
"""
