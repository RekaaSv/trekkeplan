import logging

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

    def oppdater_filter(self):
        logging.info("FilteredTable.oppdater_filter")
        self.blockSignals(True)
        # Hent verdi fra seleksjonsmodellen til <referansetabell>,
        # kun en rad fordi single select,
        # kolonne <referansekolonne>
        indexes = self.referansetabell.selectionModel().selectedIndexes()

        if indexes:
            logging.info("FilteredTable.indexes er der")
            self.filterverdi = indexes[self.referansekolonne].data()
        else:
            logging.info("FilteredTable.indexes er None")
            self.filterverdi = None
        self.blockSignals(False)

        for rad in range(self.rowCount()):
            match = self.rad_er_valgbar(rad)
            self.set_rad_valgbar(rad, match)

#        QTimer.singleShot(0, self.rens_seleksjon)
        self.rens_seleksjon()
        self.scroll_til_forste_valgbar_rad()
        logging.info("FilteredTable.oppdater_filter end")

    def set_rad_valgbar(self, rad_index, valgbar):
        logging.info("FilteredTable.set_rad_valgbar")
        self.blockSignals(True)
        lys_bla = QColor(220, 235, 255)
#        edit_colour = QColor(245, 245, 220)
        edit_colour = QColor(255, 250, 205)
        standard = QColor(Qt.white)

        for kol in range(self.columnCount()):
            item = self.item(rad_index, kol)
            if item is None:
                continue

            try:
                flags = item.flags()
                if valgbar:
                    item.setFlags(flags | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    if (kol==10 or kol==11):
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setBackground(edit_colour)
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        item.setBackground(lys_bla)
                else:
                    item.setFlags(flags & ~Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(standard)
            except Exception as e:
                logging.error(f"Feil i set_rad_valgbar på rad {rad_index}, kol {kol}: {e}")
                raise

        self.blockSignals(False)
        logging.info("FilteredTable.set_rad_valgbar end")

    def rad_er_valgbar(self, rad_index):
        logging.info("FilteredTable.rad_er_valgbar")
        er_valgbar = False
        if self.filterverdi:
            index = self.model().index(rad_index, self.filterkolonne)
            er_valgbar = index.isValid() and index.data() == self.filterverdi
        else:
            er_valgbar = False

        logging.info("FilteredTable.rad_er_valgbar end")
        return er_valgbar


    def rens_seleksjon(self):
        logging.info("FilteredTable.rens_seleksjon")
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
        logging.info("FilteredTable.rens_seleksjon end")

    def _planlagt_filteroppdatering(self):
        logging.info("FilteredTable._planlagt_filteroppdatering")
        QTimer.singleShot(0, self.oppdater_filter)

    def scroll_til_forste_valgbar_rad(self):
        logging.info("FilteredTable.scroll_til_forste_valgbar_rad")
        for rad in range(self.rowCount()):
            if self.rad_er_valgbar(rad):
                # Bruk kolonne 0 eller en annen synlig kolonne
                self.scrollToItem(self.item(rad, 2), QAbstractItemView.PositionAtTop)
                break
        logging.info("FilteredTable.scroll_til_forste_valgbar_rad end")
