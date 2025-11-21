import logging

from PyQt5.QtWidgets import QTableWidget, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer, QItemSelectionModel
from PyQt5.QtGui import QColor

class FilteredTable(QTableWidget):
    def __init__(self, ref_table, ref_column, filter_column, parent=None):
        super().__init__(parent)
        self.ref_table = ref_table
        self.ref_column = ref_column
        self.filter_column = filter_column
        self.filter_value = None

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.ref_table.itemSelectionChanged.connect(self._planned_filter_update)
        self.itemSelectionChanged.connect(self.clear_selection)

    def update_filter(self):
        logging.info("FilteredTable.oppdater_filter")
        self.blockSignals(True)
        # Hent verdi fra seleksjonsmodellen til <ref_table>,
        # kun en rad fordi single select,
        # kolonne <ref_column>
        indexes = self.ref_table.selectionModel().selectedIndexes()

        if indexes:
            logging.info("FilteredTable.indexes er der")
            self.filter_value = indexes[self.ref_column].data()
        else:
            logging.info("FilteredTable.indexes er None")
            self.filter_value = None
        self.blockSignals(False)

        for row in range(self.rowCount()):
            match = self.row_is_selectable(row)
            self.set_row_selectable(row, match)

#        QTimer.singleShot(0, parent.rens_seleksjon)
        self.clear_selection()
        self.scroll_to_first_selectable_row()
        logging.info("FilteredTable.oppdater_filter end")

    def set_row_selectable(self, row_inx, selectable):
        logging.info("FilteredTable.set_row_selectable")
        self.blockSignals(True)
        light_blue = QColor(220, 235, 255)
#        edit_colour = QColor(245, 245, 220)
        edit_colour = QColor(255, 250, 205)
        standard = QColor(Qt.white)

        for col in range(self.columnCount()):
            item = self.item(row_inx, col)
            if item is None:
                continue

            try:
                flags = item.flags()
                if selectable:
                    item.setFlags(flags | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    if (col==10 or col==11):
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setBackground(edit_colour)
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        item.setBackground(light_blue)
                else:
                    item.setFlags(flags & ~Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(standard)
            except Exception as e:
                logging.error(f"Feil i set_row_selectable på rad {row_inx}, kol {col}: {e}")
                raise

        self.blockSignals(False)
        logging.info("FilteredTable.set_row_selectable end")

    def row_is_selectable(self, rad_index):
        logging.info("FilteredTable.row_is_selectable")
        if self.filter_value:
            index = self.model().index(rad_index, self.filter_column)
            is_selectable = index.isValid() and index.data() == self.filter_value
        else:
            is_selectable = False

        logging.info("FilteredTable.row_is_selectable end")
        return is_selectable

    def clear_selection(self):
        logging.info("FilteredTable.clear_selection")
        self.blockSignals(True)
        standard = QColor(Qt.white)
        for item in self.selectedItems():
            if item is None:
                continue
            rad = item.row()
            if not self.row_is_selectable(rad):
                index = self.indexFromItem(item)
                if index.isValid():
                    self.selectionModel().select(index, QItemSelectionModel.Deselect)
                    # Fjern visuell markering
                    for col in range(self.columnCount()):
                        cell = self.item(rad, col)
                        if cell:
                            cell.setBackground(standard)
        self.blockSignals(False)
        logging.info("FilteredTable.clear_selection end")

    def _planned_filter_update(self):
        logging.info("FilteredTable._planned_filter_update")
        QTimer.singleShot(0, self.update_filter)

    def scroll_to_first_selectable_row(self):
        logging.info("FilteredTable.scroll_to_first_selectable_row")
        for row in range(self.rowCount()):
            if self.row_is_selectable(row):
                # Bruk kolonne 0 eller en annen synlig kolonne
                self.scrollToItem(self.item(row, 2), QAbstractItemView.PositionAtTop)
                break
        logging.info("FilteredTable.scroll_to_first_selectable_row end")
