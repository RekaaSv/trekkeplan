from PyQt5.QtWidgets import QTableWidget, QAbstractItemView
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt

class FilteredTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_verdier = {}  # kol_index → ønsket verdi
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def sett_filter(self, kol_index, verdi):
        self.filter_verdier[kol_index] = verdi
        self.marker_valgbare_rader()

    def mousePressEvent(self, event):
        indeks = self.indexAt(event.pos())
        rad = indeks.row()

        if self.rad_oppfyller_filter(rad):
            super().mousePressEvent(event)
        else:
            self.clearSelection()

    # Kun velge rad med mus, ikke tastatur.
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.clearSelection()

    def rad_oppfyller_filter(self, rad):
        if not self.filter_verdier:
            return False  # ingen filter = ingen valgbarhet

        for kol_index, ønsket in self.filter_verdier.items():
            celle = self.item(rad, kol_index)
            if not celle or celle.text() != ønsket:
                return False
        return True

    def marker_valgbare_rader(self):
        lys_bla = QBrush(QColor(220, 235, 255))
        hvit = QBrush(Qt.white)
        første_valgbar = None

        for rad in range(self.rowCount()):
            bakgrunn = lys_bla if self.rad_oppfyller_filter(rad) else hvit
            for kol in range(self.columnCount()):
                celle = self.item(rad, kol)
                if celle:
                    celle.setBackground(bakgrunn)

            if bakgrunn == lys_bla and første_valgbar is None:
                første_valgbar = self.item(rad, 0)

        if første_valgbar:
            self.scrollToItem(første_valgbar, QAbstractItemView.PositionAtTop)

