import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QTableWidget, QHBoxLayout, QTableWidgetItem, QMenu, QAction, QLabel, QPushButton, \
    QVBoxLayout

from db import queries


class SplitClubMates(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.info("SplitClubMates")
        self.parent = parent
        self.setWindowTitle("Splitt klubbkompiser")
#        self.resize(1000, 700)
        self.resize(1287, 707)

        self.setFont(parent.font())  # arver font fra hovedvinduet

        # Tabeller
        self.left_columns = [0, 0, 0, 80, 200, 250, 70]
        self.venstre = QTableWidget()
        self.venstre.setSelectionBehavior(QTableWidget.SelectRows)
        self.venstre.setSelectionMode(QTableWidget.SingleSelection)
        self.venstre.verticalHeader().setVisible(False)
        self.venstre.setContextMenuPolicy(Qt.CustomContextMenu)
        self.venstre.customContextMenuRequested.connect(self.menu_draw_class)
        self.venstre.horizontalHeader().setStyleSheet(self.parent.table_header_style_sheet)

        parent.keep_selection_colour(self.venstre)

        self.right_columns = [0, 0, 80, 200, 250, 70]
        self.hoyre = QTableWidget()
        self.hoyre.setSelectionBehavior(QTableWidget.SelectRows)
        self.hoyre.verticalHeader().setVisible(False)
        self.hoyre.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hoyre.customContextMenuRequested.connect(self.menu_swap_times)
        self.hoyre.horizontalHeader().setStyleSheet(self.parent.table_header_style_sheet)
        parent.keep_selection_colour(self.hoyre)



        # Overskrifter
#        venstre_label = QLabel("🔍 Klubbkamerater rett etter hverandre")
        venstre_label = self.get_label("Løpere med klubbkamerat rett før")
        venstre_label.setStyleSheet(parent.style_table_header)

        hoyre_label = self.get_label("Startrekkefølge (bytte starttider)")
        hoyre_label.setStyleSheet(parent.style_table_header)

        # Knapper
        self.refresh_button = QPushButton("Oppfrisk")
        self.refresh_button.setStyleSheet(self.parent.button_style)

        self.close_button = QPushButton("Avslutt")
        self.close_button.setStyleSheet(self.parent.button_style)

        self.refresh_button.clicked.connect(self.refresh_left)
        self.close_button.clicked.connect(self.close)

        self.venstre.itemSelectionChanged.connect(self.refresh_right)

        # Layout: hovedboks
        hoved_layout = QVBoxLayout()

        # Midtboks
        midtboks = QHBoxLayout()

        # Tabellbunnboks
        tabellbunn_boks = QHBoxLayout()
        tabellbunn_boks.addWidget(self.refresh_button)
        tabellbunn_boks.addStretch()

        # Venstreboks
        venstre_boks = QVBoxLayout()
        venstre_boks.addWidget(venstre_label)
        venstre_boks.addWidget(self.venstre)
        venstre_boks.addLayout(tabellbunn_boks)
#        venstre_boks.addWidget(self.refresh_button, Qt.AlignLeft)
        venstre_boks.addStretch()

        # Høyreboks
        hoyre_boks = QVBoxLayout()
        hoyre_boks.addWidget(hoyre_label)
        hoyre_boks.addWidget(self.hoyre)
        hoyre_boks.addStretch()

        midtboks.addLayout(venstre_boks)
        midtboks.addLayout(hoyre_boks)

        # Bunnboks
        bunnboks = QHBoxLayout()
        bunnboks.addStretch()
        bunnboks.addWidget(self.close_button)

        # Sett sammen
        hoved_layout.addLayout(midtboks)
        hoved_layout.addLayout(bunnboks)
        self.setLayout(hoved_layout)

        self.venstre.setColumnHidden(0, True)
        self.venstre.setColumnHidden(1, True)
        self.venstre.setColumnHidden(2, True)
        self.hoyre.setColumnHidden(0, True)
        self.hoyre.setColumnHidden(1, True)

        parent.keep_selection_colour(self)

        self.refresh_left()

        # Kontekstmeny med funksjonstast.
        self.menu_right = QMenu(self)
        self.swap_action = QAction("Bytt starttider", self)
        self.menu_right.addAction(self.swap_action)
        self.hoyre.addAction(self.swap_action)
        self.swap_action.setShortcut("F9")
        self.swap_action.triggered.connect(lambda: self.swap_start_times())

        self.menu_left = QMenu(self)
        self.redraw_action = QAction("Trekk denne klassen om igjen", self)
        self.menu_left.addAction(self.redraw_action)
        self.venstre.addAction(self.redraw_action)
        self.redraw_action.setShortcut("F10")
        self.redraw_action.triggered.connect(lambda: self.draw_start_times_class())

        logging.info("SplitClubMates layout end")

    def refresh_left(self):
        logging.info("SplitClubMates.refresh_left")
        rows, columns = queries.read_club_mates(self.parent.conn_mgr, self.parent.raceId)
        logging.debug("columns: %s", columns)
        logging.debug("rows: %s", rows)

        self.parent.populate_table(self.venstre, columns, rows)

        # Dimesjoner tabellen.
        self.parent.set_table_sizes(self.venstre, self.left_columns)

        # Selekter 1. rad.
        if self.venstre.rowCount() > 0:
            self.venstre.selectRow(0)
        else:
            # Refresh høyre tabell for å få kolonner.
            self.refresh_right()

    def refresh_right(self):
        logging.info("SplitClubMates.refresh_right")
        # Finn verdier fra selektert rad i venstre tabell.
        selected = None
        model_indexes = self.venstre.selectionModel().selectedRows()
        if model_indexes:
            selected = model_indexes[0].row()
        if selected is None:
            classid = -1 # Gir 0 rader, men får kolonnene.
            previd = None
        else:
            left_id = self.venstre.item(selected, 0).text()
            previd = self.venstre.item(selected, 1).text()
            classid = self.venstre.item(selected, 2).text()
            logging.debug("_oppdater_hoyre: %s", classid)
            logging.debug("left_id: %s", left_id)

        # Populer høyre tabell.
        rows, columns = queries.read_names(self.parent.conn_mgr, classid)
        logging.debug("columns: %s", columns)
        logging.debug("rows: %s", rows)
        self.parent.populate_table(self.hoyre, columns, rows)

        # Marker radene som har id lik venstre tabell sin id eller previd.
        first_found_row_inx = None
        for rad_inx in range(self.hoyre.rowCount()):
            logging.debug("rad_inx: %s", rad_inx)
            my_id = self.hoyre.item(rad_inx, 0).text()
            logging.debug("my_id: %s", my_id)
            match = (my_id == left_id) or (my_id == previd)
            logging.debug("match: %s", match)
            if match:
                # Husk den første match'en for scrollToItem lenger ned i koden.
                if first_found_row_inx is None:
                    first_found_row_inx = rad_inx
            self.marker_rad(rad_inx, match)

        # Dimesjoner tabellen.
        self.parent.set_table_sizes(self.hoyre, self.right_columns)

        if first_found_row_inx is not None:
#            self.hoyre.scrollToItem(self.hoyre.item(first_found_row_inx, 3))
            # Feilet av og til. Lag forsinkelse med singleShot
            QTimer.singleShot(0, lambda: self.hoyre.scrollToItem(self.hoyre.item(first_found_row_inx, 3)))
            logging.info("scrollToItem, rad_inx: %s", first_found_row_inx)
        else:
            logging.info("ERROR: first_found_row_inx is None!")


    def marker_rad(self, rad_inx, match):
        logging.info("SplitClubMates.marker_rad: %s, %s", rad_inx, match)
        lys_bla = QColor(220, 235, 255)
        standard = QColor(Qt.white)

        for kol_inx in range(self.hoyre.columnCount()):
            logging.debug("kol_inx: %s", kol_inx)
            item = self.hoyre.item(rad_inx, kol_inx)
            logging.debug("item: %s", item)
            if item is None:
                continue

            if match:
                item.setBackground(lys_bla)
            else:
                item.setBackground(standard)

    def menu_draw_class(self, pos):
        rad_index = self.venstre.rowAt(pos.y())
        if rad_index < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_left.exec_(self.venstre.viewport().mapToGlobal(pos))


    def menu_swap_times(self, pos):
        rad_index = self.hoyre.rowAt(pos.y())
        if rad_index < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_right.exec_(self.hoyre.viewport().mapToGlobal(pos))

    def swap_start_times(self):
        logging.info("swap_start_times")
        model_indexes = self.hoyre.selectionModel().selectedRows()

        if len(model_indexes) != 2:
            self.parent.vis_brukermelding("Du må velge de to løperne som skal bytte starttider!")
            return
        inx1 = model_indexes[0].row()
        inx2 = model_indexes[1].row()

        id1 = self.hoyre.item(inx1, 0).text()
        id2 = self.hoyre.item(inx2, 0).text()

        logging.debug("id1: %s", id1)
        logging.debug("id2: %s", id2)
        queries.swap_start_times(self.parent.conn_mgr, id1, id2, self.parent.raceId)

        self.refresh_right()

    def draw_start_times_class(self):
        logging.info("draw_start_times_class")
        if self.parent.drawplan_changed > self.parent.draw_time:
            self.parent.vis_brukermelding("Trekkeplanen er endret etter siste trekking. Da kan du ikke trekke klassen om igjen. Du må enten gjøre hovedtrekkingen på nytt, eller bruke metoden med bytting av starttider i høyre tabell.")
            return

        model_indexes = self.venstre.selectionModel().selectedRows()
        if len(model_indexes) != 1:
            self.parent.vis_brukermelding("Du må velge en rad å omtrekke starttider for!")
            return
        inx = model_indexes[0].row()
        class_id = self.venstre.item(inx, 2).text()

        queries.draw_start_times_class(self.parent.conn_mgr, class_id)
        self.refresh_left()
        self.parent.select_by_id(self.venstre, class_id, 2)

    def get_label(self,tekst):
        lable = QLabel(tekst)
        font = lable.font()
        font.setBold(True)
        font.setPointSize(11)
        lable.setFont(font)
        return lable

    def closeEvent(self, event):
        size = self.size()
        logging.info(f"Vinduet avsluttes med størrelse: {size.width()} x {size.height()}")
        super().closeEvent(event)
