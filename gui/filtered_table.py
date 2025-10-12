from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer, QItemSelectionModel
from PyQt5.QtGui import QColor

class FilteredTable(QTableWidget):
    def __init__(self, referansetabell, referansekolonne, filterkolonne, parent=None):
        super().__init__(parent)
        self.referansetabell = referansetabell
        self.referansekolonne = referansekolonne
        self.filterkolonne = filterkolonne
        self.filterverdi = None

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.referansetabell.itemSelectionChanged.connect(self._planlagt_filteroppdatering)
        self.itemSelectionChanged.connect(self.rens_seleksjon)
        self.log = True

    def oppdater_filter(self):
        if self.log: print("FilteredTable.oppdater_filter")
        self.blockSignals(True)
        # Hent verdi fra seleksjonsmodellen til <referansetabell>,
        # kun en rad fordi single select,
        # kolonne <referansekolonne>
        indexes = self.referansetabell.selectionModel().selectedIndexes()

#        print(f"indexes: {indexes}")
#        rad = indexes[0].row()
#        kol = indexes[0].column()
        if indexes:
            if self.log: print("FilteredTable.indexes er der")
            self.filterverdi = indexes[self.referansekolonne].data()
        else:
            if self.log: print("FilteredTable.indexes er None")
            self.filterverdi = None
        self.blockSignals(False)

#        print(f"Rad {rad}, kol {kol}, verdi: {self.filterverdi}")
#        self.filterverdi = verdi

#        items = self.referansetabell.selectedItems()
#        self.filterverdi = items[0].text() if items else None

        for rad in range(self.rowCount()):
            match = self.rad_er_valgbar(rad)

#            item = self.item(rad, 1)
#            match = item and item.text() == self.filterverdi
            self.set_rad_valgbar(rad, match)

#        QTimer.singleShot(0, self.rens_seleksjon)
        self.rens_seleksjon()
        self.scroll_til_forste_valgbar_rad()
        if self.log: print("FilteredTable.oppdater_filter end")

    def set_rad_valgbar(self, rad_index, valgbar):
        if self.log: print("FilteredTable.set_rad_valgbar")
        self.blockSignals(True)
        lys_bla = QColor(220, 235, 255)
        standard = QColor(Qt.white)

        for kol in range(self.columnCount()):
            item = self.item(rad_index, kol)
            if item is None:
                continue

            try:
                index = self.indexFromItem(item)
#                if self.selectionModel().isSelected(index):
#                    self.setItemSelected(item, False)
                flags = item.flags()
                if valgbar:
                    item.setFlags(flags | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setBackground(lys_bla)
                else:
                    item.setFlags(flags & ~Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setBackground(standard)
            except Exception as e:
                print(f"Feil i set_rad_valgbar på rad {rad_index}, kol {kol}: {e}")

        self.blockSignals(False)
        if self.log: print("FilteredTable.set_rad_valgbar end")

    def rad_er_valgbar(self, rad_index):
        if self.log: print("FilteredTable.rad_er_valgbar")
        er_valgbar = False
        if self.filterverdi:
#            if self.log: print("rad_er_valgbar 1")
#            if self.log: print("self.filterverdi =" + self.filterverdi)
            index = self.model().index(rad_index, self.filterkolonne)
#            if self.log: print("rad_er_valgbar 2")
            er_valgbar = index.isValid() and index.data() == self.filterverdi
#            if self.log: print("rad_er_valgbar 3")
        else:
#            if self.log: print("rad_er_valgbar 4")
            er_valgbar = False
 #           if self.log: print("rad_er_valgbar 5")

#        if self.log:
#            if self.log: print("rad_er_valgbar 6")
#            if er_valgbar: print("rad_er_valgbar = True")
#            else: print("rad_er_valgbar = False")

        if self.log: print("FilteredTable.rad_er_valgbar end")
        return er_valgbar


    def rens_seleksjon(self):
        if self.log: print("FilteredTable.rens_seleksjon")
        self.blockSignals(True)
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
        self.blockSignals(False)
        if self.log: print("FilteredTable.rens_seleksjon end")

    def _planlagt_filteroppdatering(self):
        if self.log: print("FilteredTable._planlagt_filteroppdatering")
        QTimer.singleShot(0, self.oppdater_filter)

    def scroll_til_forste_valgbar_rad(self):
        if self.log: print("FilteredTable.scroll_til_forste_valgbar_rad")
        for rad in range(self.rowCount()):
            if self.rad_er_valgbar(rad):
                # Bruk kolonne 0 eller en annen synlig kolonne
                self.scrollToItem(self.item(rad, 2), QAbstractItemView.PositionAtTop)
                break
        if self.log: print("FilteredTable.scroll_til_forste_valgbar_rad end")
