from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QTableWidget, QHBoxLayout, QTableWidgetItem, QMenu, QAction

from db import queries


class SplitClubMates(QDialog):
    def __init__(self, rows, columns, klasse_data_func, parent=None):
        super().__init__(parent)
        if parent.log: print("SplitClubMates")
        self.parent = parent
        self.setWindowTitle("SplitClubMates")
        self.resize(1500, 700)

        self.venstre = QTableWidget()
        self.venstre.setSelectionBehavior(QTableWidget.SelectRows)
        self.venstre.setSelectionMode(QTableWidget.SingleSelection)
        self.venstre.verticalHeader().setVisible(False)

        self.hoyre = QTableWidget()
        self.hoyre.setSelectionBehavior(QTableWidget.SelectRows)
        self.hoyre.verticalHeader().setVisible(False)
        self.hoyre.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hoyre.customContextMenuRequested.connect(self.menu_swap_times)

        if parent.log: print("SplitClubMates")
        parent.populate_table(self.venstre, columns, rows)
#        self._populate_venstre(problem_liste)
        self.venstre.itemSelectionChanged.connect(self._oppdater_hoyre)

        layout = QHBoxLayout()
        layout.addWidget(self.venstre)
        layout.addWidget(self.hoyre)
        self.setLayout(layout)

        self.venstre.setColumnHidden(0, True)
        self.venstre.setColumnHidden(1, True)
        self.venstre.setColumnHidden(2, True)

        parent.keep_selection_colour(self)

        if self.venstre.rowCount() > 0:
            self.venstre.selectRow(0)

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
        # Finn verdier fra selektert rad.
#        selected = self.venstre.currentRow()

        selected = None
        model_indexes = self.venstre.selectionModel().selectedRows()
        if model_indexes:
            selected = model_indexes[0].row()
        if selected is None:
            self.hoyre.clear()
            self.hoyre.setRowCount(0)
            self.hoyre.setColumnCount(0)
            return

        left_id = self.venstre.item(selected, 0).text()
        previd = self.venstre.item(selected, 1).text()
        classid = self.venstre.item(selected, 2).text()
        if self.parent.log: print("_oppdater_hoyre", classid)
        if self.parent.log: print("left_id", left_id)

        # Populer høyre tabell.
        rows, columns = queries.read_names(self.parent.conn_mgr, classid)
        if self.parent.log: print("columns", columns)
        if self.parent.log: print("rows", rows)
        self.parent.populate_table(self.hoyre, columns, rows)

        # Marker radene med id og previd.
        first_found_row_inx = None
        for rad_inx in range(self.hoyre.rowCount()):
            print("rad_inx", rad_inx)
            my_id = self.hoyre.item(rad_inx, 0).text()
            print("my_id", my_id)
            match = (my_id == left_id) or (my_id == previd)
            print("match", match)
            if match:
                if first_found_row_inx is None:
#                    self.hoyre.scrollToItem(self.hoyre.item(rad_inx, 3))
#                    QTimer.singleShot(0, lambda: self.hoyre.scrollToItem(self.hoyre.item(rad_inx, 0)))
                    first_found_row_inx = rad_inx
            self.marker_rad(rad_inx, match)

        self.hoyre.setColumnHidden(0, True)
        self.hoyre.setColumnHidden(1, True)

        if first_found_row_inx is not None:
#            self.hoyre.scrollToItem(self.hoyre.item(first_found_row_inx, 3))
            QTimer.singleShot(0, lambda: self.hoyre.scrollToItem(self.hoyre.item(first_found_row_inx, 3)))
            print("scrollToItem, rad_inx", first_found_row_inx)
        else:
            print("ERROR: first_found_row_inx is None!")

    def marker_rad(self, rad_inx, match):
        if self.parent.log: print("SplitClubMates.marker_rad", rad_inx, match)
        lys_bla = QColor(220, 235, 255)
        standard = QColor(Qt.white)

        for kol_inx in range(self.hoyre.columnCount()):
            if self.parent.log: print("kol_inx", kol_inx)
            item = self.hoyre.item(rad_inx, kol_inx)
            if self.parent.log: print("item", item)
            if item is None:
                continue

            if match:
                item.setBackground(lys_bla)
            else:
                item.setBackground(standard)

    def menu_swap_times(self, pos):
        rad_index = self.hoyre.rowAt(pos.y())
        if rad_index < 0:
            print("Ingen rad under musepeker – meny avbrytes")
            return

        meny = QMenu(self)
        swap_times = QAction("Bytt starttider", self)
        swap_times.triggered.connect(lambda: self.swap_start_times())
        meny.addAction(swap_times)

        meny.exec_(self.hoyre.viewport().mapToGlobal(pos))

    def swap_start_times(self):
        print("swap_start_times")
        model_indexes = self.hoyre.selectionModel().selectedRows()

        if len(model_indexes) != 2:
            self.parent.vis_brukermelding("Du må velge nøyaktig to rader. Det er disse to som skal bytte starttider!")
        inx1 = model_indexes[0].row()
        inx2 = model_indexes[1].row()

        id1 = self.hoyre.item(inx1, 0).text()
        id2 = self.hoyre.item(inx2, 0).text()

        print("id1", id1)
        print("id2", id2)
        queries.swap_start_times(self.parent.conn_mgr, id1, id2, self.parent.raceId)

        self._oppdater_hoyre()

