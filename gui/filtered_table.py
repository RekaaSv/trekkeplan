from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer, QItemSelectionModel
from PyQt5.QtGui import QColor

class FilteredTable(QTableWidget):
    def __init__(self, referansetabell, referansekolonne, parent=None):
        super().__init__(parent)
        self.referansetabell = referansetabell
        self.referansekolonne = referansekolonne
        self.filterverdi = None

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.referansetabell.itemSelectionChanged.connect(self._planlagt_filteroppdatering)
        self.itemSelectionChanged.connect(self.rens_seleksjon)

    def oppdater_filter(self):
        print("oppdater_filter start")
        items = self.referansetabell.selectedItems()
        self.filterverdi = items[0].text() if items else None

        for rad in range(self.rowCount()):
            item = self.item(rad, 1)
            match = item and item.text() == self.filterverdi
            self.set_rad_valgbar(rad, match)

#        QTimer.singleShot(0, self.rens_seleksjon)
        self.rens_seleksjon()
        self.scroll_til_forste_valgbar_rad()
        print("oppdater_filter end")

    def set_rad_valgbar(self, rad_index, valgbar):
        print("set_rad_valgbar start")
        lys_bla = QColor(220, 235, 255)
        standard = QColor(Qt.white)

        for kol in range(self.columnCount()):
            item = self.item(rad_index, kol)
            if item is None:
                continue

            try:
                index = self.indexFromItem(item)
                if self.selectionModel().isSelected(index):
                    self.setItemSelected(item, False)

                flags = item.flags()
                if valgbar:
                    item.setFlags(flags | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setBackground(lys_bla)
                else:
                    item.setFlags(flags & ~Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setBackground(standard)
            except Exception as e:
                print(f"Feil i set_rad_valgbar på rad {rad_index}, kol {kol}: {e}")

        print("set_rad_valgbar end")

    def rad_er_valgbar(self, rad_index):
        item = self.item(rad_index, 1)
        return item and item.text() == self.filterverdi

    def rens_seleksjon(self):
        print("rens_seleksjon start")
        standard = QColor(Qt.white)
        for item in self.selectedItems():
            if item is None:
                continue
            rad = item.row()
            if not self.rad_er_valgbar(rad):
                index = self.indexFromItem(item)
                if index.isValid():
                    self.selectionModel().select(index, QItemSelectionModel.Deselect)
                    # Fjern visuell markering
                    for kol in range(self.columnCount()):
                        celle = self.item(rad, kol)
                        if celle:
                            celle.setBackground(standard)

#                    self.marker_rad(index, QColor(Qt.white))
        print("rens_seleksjon end")

    def _planlagt_filteroppdatering(self):
        QTimer.singleShot(0, self.oppdater_filter)

    def marker_rad(rad_index, farge):
        for kol in range(self.columnCount()):
            item = self.item(rad_index, kol)
            if item:
                item.setBackground(farge)

    def scroll_til_forste_valgbar_rad(self):
        for rad in range(self.rowCount()):
            if self.rad_er_valgbar(rad):
                self.scrollToItem(self.item(rad, 0), QAbstractItemView.PositionAtTop)
                break
