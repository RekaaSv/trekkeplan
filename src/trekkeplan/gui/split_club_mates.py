import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QTableWidget, QHBoxLayout, QMenu, QAction, QLabel, QPushButton, \
    QVBoxLayout

from trekkeplan.db import sql


class SplitClubMates(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.info("SplitClubMates")
        self.parent = parent
        self.setWindowTitle("Splitt klubbkamerater")
#        parent.resize(1000, 700)
        self.resize(1287, 707)

        self.setFont(parent.font())  # arver font fra hovedvinduet

        # Tabeller
        self.left_columns = [0, 0, 0, 80, 200, 250, 70]
        self.table_club_mates = QTableWidget()
        self.table_club_mates.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_club_mates.setSelectionMode(QTableWidget.SingleSelection)
        self.table_club_mates.verticalHeader().setVisible(False)
        self.table_club_mates.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_club_mates.customContextMenuRequested.connect(self.menu_draw_class)
        self.table_club_mates.horizontalHeader().setStyleSheet(self.parent.table_header_style_sheet)
        self.table_club_mates.setStyleSheet(self.parent.table_style_sheet)

        parent.keep_selection_colour(self.table_club_mates)

        self.right_columns = [0, 0, 80, 200, 250, 70]
        self.table_class_startlist = QTableWidget()
        self.table_class_startlist.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_class_startlist.verticalHeader().setVisible(False)
        self.table_class_startlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_class_startlist.customContextMenuRequested.connect(self.menu_swap_times)
        self.table_class_startlist.horizontalHeader().setStyleSheet(self.parent.table_header_style_sheet)
        self.table_class_startlist.setStyleSheet(self.parent.table_style_sheet)
        parent.keep_selection_colour(self.table_class_startlist)

        # Overskrifter
        label_club_mates = QLabel("Løpere med klubbkamerat rett før")
        label_club_mates.setStyleSheet(parent.style_table_header)

        label_startlist = QLabel("Startrekkefølge (bytte starttider)")
        label_startlist.setStyleSheet(parent.style_table_header)

        # Knapper
        self.refresh_button = QPushButton("Oppfrisk")
        self.refresh_button.setStyleSheet(self.parent.button_style)

        self.close_button = QPushButton("Avslutt")
        self.close_button.setStyleSheet(self.parent.button_style)

        self.refresh_button.clicked.connect(self.refresh_left)
        self.close_button.clicked.connect(self.close)

        self.table_club_mates.itemSelectionChanged.connect(self.refresh_right)

        # Layout: hovedboks
        layout_main = QVBoxLayout()

        # Midtboks
        layout_center = QHBoxLayout()

        # Tabellbunnboks
        layout_left_below_table = QHBoxLayout()
        layout_left_below_table.addWidget(self.refresh_button)
        layout_left_below_table.addStretch()

        # Venstreboks
        layout_left_column = QVBoxLayout()
        layout_left_column.addWidget(label_club_mates)
        layout_left_column.addWidget(self.table_club_mates)
        layout_left_column.addLayout(layout_left_below_table)
#        venstre_boks.addWidget(parent.refresh_button, Qt.AlignLeft)
        layout_left_column.addStretch()

        # Høyreboks
        layout_right_column = QVBoxLayout()
        layout_right_column.addWidget(label_startlist)
        layout_right_column.addWidget(self.table_class_startlist)
        layout_right_column.addStretch()

        layout_center.addLayout(layout_left_column)
        layout_center.addLayout(layout_right_column)

        # Bunnboks
        layout_bottom = QHBoxLayout()
        layout_bottom.addStretch()
        layout_bottom.addWidget(self.close_button)

        # Sett sammen
        layout_main.addLayout(layout_center)
        layout_main.addLayout(layout_bottom)
        self.setLayout(layout_main)

        self.table_club_mates.setColumnHidden(0, True)
        self.table_club_mates.setColumnHidden(1, True)
        self.table_club_mates.setColumnHidden(2, True)
        self.table_class_startlist.setColumnHidden(0, True)
        self.table_class_startlist.setColumnHidden(1, True)

        parent.keep_selection_colour(self)

        self.refresh_left()

        # Kontekstmeny med funksjonstast.
        self.menu_right = QMenu(self)
        self.swap_action = QAction("Bytt starttider", self)
        self.menu_right.addAction(self.swap_action)
        self.table_class_startlist.addAction(self.swap_action)
        self.swap_action.setShortcut("F9")
        self.swap_action.triggered.connect(lambda: self.swap_start_times())

        self.menu_left = QMenu(self)
        self.redraw_action = QAction("Trekk denne klassen om igjen", self)
        self.menu_left.addAction(self.redraw_action)
        self.table_club_mates.addAction(self.redraw_action)
        self.redraw_action.setShortcut("F10")
        self.redraw_action.triggered.connect(lambda: self.draw_start_times_class())

        logging.info("SplitClubMates layout end")

    def refresh_left(self):
        logging.info("SplitClubMates.refresh_left")
        rows, columns = sql.read_club_mates(self.parent.conn_mgr, self.parent.race_id)
        logging.debug("columns: %s", columns)
        logging.debug("rows: %s", rows)

        self.parent.populate_table(self.table_club_mates, columns, rows)

        # Dimesjoner tabellen.
        self.parent.set_table_sizes(self.table_club_mates, self.left_columns)

        # Selekter 1. rad.
        if self.table_club_mates.rowCount() > 0:
            self.table_club_mates.selectRow(0)
        else:
            # Refresh høyre table for å få kolonner.
            self.refresh_right()

    def refresh_right(self):
        logging.info("SplitClubMates.refresh_right")
        # Finn verdier fra selektert rad i table_club_mates table.
        selected = None
        model_indexes = self.table_club_mates.selectionModel().selectedRows()
        if model_indexes:
            selected = model_indexes[0].row()
        if selected is None:
            classid = -1 # Gir 0 rader, men får kolonnene.
            previd = None
        else:
            left_id = self.table_club_mates.item(selected, 0).text()
            previd = self.table_club_mates.item(selected, 1).text()
            classid = self.table_club_mates.item(selected, 2).text()
            logging.debug("_oppdater_hoyre: %s", classid)
            logging.debug("left_id: %s", left_id)

        # Populer høyre table.
        rows, columns = sql.read_names(self.parent.conn_mgr, classid)
        logging.debug("columns: %s", columns)
        logging.debug("rows: %s", rows)
        self.parent.populate_table(self.table_class_startlist, columns, rows)

        # Marker radene som har id lik table_club_mates table sin id eller previd.
        first_found_row_inx = None
        for row_inx in range(self.table_class_startlist.rowCount()):
            logging.debug("row_inx: %s", row_inx)
            my_id = self.table_class_startlist.item(row_inx, 0).text()
            logging.debug("my_id: %s", my_id)
            match = (my_id == left_id) or (my_id == previd)
            logging.debug("match: %s", match)
            if match:
                # Husk den første match'en for scrollToItem lenger ned i koden.
                if first_found_row_inx is None:
                    first_found_row_inx = row_inx
            self.mark_row(row_inx, match)

        # Dimesjoner tabellen.
        self.parent.set_table_sizes(self.table_class_startlist, self.right_columns)

        if first_found_row_inx is not None:
#            parent.table_class_startlist.scrollToItem(parent.table_class_startlist.item(first_found_row_inx, 3))
            # Feilet av og til. Lag forsinkelse med singleShot
            QTimer.singleShot(0, lambda: self.table_class_startlist.scrollToItem(self.table_class_startlist.item(first_found_row_inx, 3)))
            logging.info("scrollToItem, row_inx: %s", first_found_row_inx)
        else:
            logging.info("ERROR: first_found_row_inx is None!")


    def mark_row(self, row_inx, match):
        logging.info("SplitClubMates.marker_rad: %s, %s", row_inx, match)
        light_blue = QColor(220, 235, 255)
        standard = QColor(Qt.white)

        for col_inx in range(self.table_class_startlist.columnCount()):
            logging.debug("col_inx: %s", col_inx)
            item = self.table_class_startlist.item(row_inx, col_inx)
            logging.debug("item: %s", item)
            if item is None:
                continue

            if match:
                item.setBackground(light_blue)
            else:
                item.setBackground(standard)

    def menu_draw_class(self, pos):
        row_inx = self.table_club_mates.rowAt(pos.y())
        if row_inx < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_left.exec_(self.table_club_mates.viewport().mapToGlobal(pos))


    def menu_swap_times(self, pos):
        row_inx = self.table_class_startlist.rowAt(pos.y())
        if row_inx < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_right.exec_(self.table_class_startlist.viewport().mapToGlobal(pos))

    def swap_start_times(self):
        logging.info("swap_start_times")
        model_indexes = self.table_class_startlist.selectionModel().selectedRows()

        if len(model_indexes) != 2:
            self.parent.show_message("Du må velge de to løperne som skal bytte starttider!")
            return
        inx1 = model_indexes[0].row()
        inx2 = model_indexes[1].row()

        id1 = self.table_class_startlist.item(inx1, 0).text()
        id2 = self.table_class_startlist.item(inx2, 0).text()

        logging.debug("id1: %s", id1)
        logging.debug("id2: %s", id2)
        sql.swap_start_times(self.parent.conn_mgr, id1, id2, self.parent.race_id)

        self.refresh_right()

    def draw_start_times_class(self):
        logging.info("draw_start_times_class")
        if self.parent.drawplan_changed > self.parent.draw_time:
            self.parent.show_message("Trekkeplanen er endret etter siste trekking. Da kan du ikke trekke klassen om igjen. Du må enten gjøre hovedtrekkingen på nytt, eller bruke metoden med bytting av starttider i høyre table.")
            return

        model_indexes = self.table_club_mates.selectionModel().selectedRows()
        if len(model_indexes) != 1:
            self.parent.show_message("Du må velge en rad å omtrekke starttider for!")
            return
        inx = model_indexes[0].row()
        class_id = self.table_club_mates.item(inx, 2).text()

        sql.draw_start_times_class(self.parent.conn_mgr, class_id)
        self.refresh_left()
        self.parent.select_by_id(self.table_club_mates, class_id, 2)

    def get_label(self,tekst):
        label = QLabel(tekst)
        font = label.font()
        font.setBold(True)
        font.setPointSize(11)
        label.setFont(font)
        return label

    def closeEvent(self, event):
        size = self.size()
        logging.info(f"Vinduet avsluttes med størrelse: {size.width()} x {size.height()}")
        super().closeEvent(event)
