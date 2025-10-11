from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, \
    QHeaderView, QTimeEdit, QMenu, QAction, QMessageBox, QLineEdit, QDialog, QDateEdit
from PyQt5.QtCore import Qt, QItemSelectionModel, QTime
from PyQt5.QtGui import QPalette, QColor, QIntValidator

import db.queries
from control import control
from control.errors import MyCustomError
from db import queries

from db.connection import get_connection
from gui.filtered_table import FilteredTable
from gui.table_connection import TableConnection
from gui.velg_løp_dialog import SelectRaceDialog


class MainWindow(QWidget):
    def __init__(self, conn, raceid):
        super().__init__()
        self.conn = conn # Lagre connection. Nei den funker ikke i andre tråer (signal, etc.)
        self.raceId = raceid
        self.str_new_first_start = None
        self.setGeometry(0, 0, 1800, 900)

        #
        # Komponenter
        #
#        self.status = QLabel("Status: Ikke tilkoblet")
        style_table_header = "font-weight: bold; font-size: 16px; margin: 10px 0;"
        title_non_planned = QLabel("Ikke-planlagte klasser")
        title_non_planned.setStyleSheet(style_table_header)
        title_block_lag = QLabel("Bås/tidsslep/gap")
        title_block_lag.setStyleSheet(style_table_header)
        title_class_start = QLabel("Trekkeplan")
        title_class_start.setStyleSheet(style_table_header)
        title_first_start = QLabel("Første start:")
        title_first_start.setStyleSheet(style_table_header)

        self.tableNotPlanned = QTableWidget()
        self.tableNotPlanned.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableNotPlanned.setMinimumSize(300, 100)
        self.tableNotPlanned.setMaximumSize(300, 800)
        self.tableNotPlanned.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableNotPlanned.verticalHeader().setVisible(False)
        self.tableNotPlanned.setSortingEnabled(True)
        self.tableNotPlanned.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableNotPlanned.customContextMenuRequested.connect(self.not_planned_menu)

        self.tableBlockLag = QTableWidget()
        self.tableBlockLag.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableBlockLag.setMinimumSize(210, 100)
        self.tableBlockLag.setMaximumSize(210, 800)
        self.tableBlockLag.setSelectionMode(QTableWidget.SingleSelection)
        self.tableBlockLag.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBlockLag.verticalHeader().setVisible(False)
        self.tableBlockLag.setSortingEnabled(True)
        self.tableBlockLag.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableBlockLag.customContextMenuRequested.connect(self.block_lag_menu)

        self.tableClassStart = FilteredTable(self.tableBlockLag, 0, 1)  #QTableWidget()
        self.tableClassStart.setMinimumSize(800, 100)
        self.tableClassStart.setMaximumSize(800, 1200)
        self.tableClassStart.setSelectionMode(QTableWidget.SingleSelection)
        self.tableClassStart.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableClassStart.verticalHeader().setVisible(False)
        self.tableClassStart.setSortingEnabled(False)
        self.tableClassStart.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableClassStart.customContextMenuRequested.connect(self.class_start_menu)

        self.raceButton = QPushButton("Velg løp")
        self.raceButton.setFixedWidth(150)
        self.raceButton.setToolTip("Velg et annet løp.")
        self.raceButton.clicked.connect(self.select_race)

 #       print("raceButton", self.raceButton.sizeHint().height())

        self.empty_hight = QWidget()
        self.empty_hight.setFixedHeight(self.raceButton.sizeHint().height())
#        self.empty_hight.setFixedHeight(50)
        self.empty_hight.setFixedWidth(100)

        self.moveButton = QPushButton("==>")
        self.moveButton.setFixedWidth(100)
#        self.moveButton.setEnabled(False)  # deaktivert til å begynne med
        self.moveButton.setToolTip("Legg til en ny bås/slep med vedier fra feltene over.\nHvis du har valgt ut en rad i tabellen under,\nvil bås feltet bli hentet herfra.")
        self.moveButton.clicked.connect(self.move_class_to_plan)

        self.addBlockButton = QPushButton("+")
        self.addBlockButton.setFixedWidth(120)
        self.addBlockButton.setToolTip("Legg til en ny bås/slep med vedier fra feltene over.\nHvis du har valgt ut en rad i tabellen under,\nvil bås feltet bli hentet herfra.")
        self.addBlockButton.clicked.connect(self.add_block_lag)
        self.drawButton = QPushButton("Trekk starttider").setFixedWidth(100)
        self.chk1Button = QPushButton("Klasser, løyper, post1")
        self.chk2Button = QPushButton("Sjekk samtidige")

        #        self.load_button.clicked.connect(self.load_data)
        #
        # Les fra MySQL initielt.
        #
        print("refresh 1", self.raceId)
        self.refresh_first_start(self.raceId)
        print("refresh 1 ferdig")

#        self.setWindowTitle(self.race_name + "   " + self.race_date_str + "             Trekkeplan")
        self.setWindowTitle("Brikkesys Trekkeplan - " + self.race_name + "   " + self.race_date_str )

        self.label_first_start = QLabel("Første start: ")
        self.field_first_start = QTimeEdit()
        self.field_first_start.setDisplayFormat("HH:mm")
        self.field_first_start.setFixedWidth(70)
        self.field_first_start.editingFinished.connect(self.first_start_edited)
        self.field_first_start.setTime(self.q_time)

        self.field_block = QLineEdit()
        self.field_block.setReadOnly(False)
        self.field_block.setFixedWidth(60)
        self.field_lag = QLineEdit()
        self.field_lag.setReadOnly(False)
        self.field_lag.setFixedWidth(40)
        self.field_lag.setValidator(QIntValidator(0, 999))
        self.field_lag.setText("0")
        self.field_gap = QLineEdit()
        self.field_gap.setReadOnly(False)
        self.field_gap.setFixedWidth(40)
        self.field_gap.setValidator(QIntValidator(0, 999))
        self.field_gap.setText("60")

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableBlockLag)
        control.refresh_table(self, self.tableClassStart)

        self.tableNotPlanned.setColumnHidden(0, True)
        self.tableNotPlanned.sortItems(1, order=Qt.AscendingOrder)
        self.tableNotPlanned.resizeColumnsToContents()
        self.tableNotPlanned.resizeRowsToContents()
        header = self.tableNotPlanned.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.tableBlockLag.setColumnHidden(0, True)
        self.tableBlockLag.setColumnHidden(1, True)
        self.tableBlockLag.sortItems(2, order=Qt.AscendingOrder)
        self.tableBlockLag.resizeColumnsToContents()
        self.tableBlockLag.resizeRowsToContents()
        header2 = self.tableBlockLag.horizontalHeader()
        header2.setSectionResizeMode(1, QHeaderView.Stretch)

        self.tableClassStart.setColumnHidden(0, True)
        self.tableClassStart.setColumnHidden(1, True)
        self.tableClassStart.resizeColumnsToContents()
        self.tableClassStart.resizeRowsToContents()
        header3 = self.tableClassStart.horizontalHeader()
        header3.setSectionResizeMode(1, QHeaderView.Stretch)

        # Behold samme farge når tabell ikke er i fokus.
        self.keep_selection_colour()
        #        self.keep_selection_colour(self.tableBlockLag)
        #        self.keep_selection_colour(self.tableClassStart)

        #
        # Layout
        #
        main_layout = QHBoxLayout()
        column1_layout = QVBoxLayout()
        column2_layout = QVBoxLayout()
        new_blocklag_layout = QHBoxLayout()
        column3_layout = QVBoxLayout()
        column4_layout = QVBoxLayout()

        column1_layout.addWidget(self.raceButton)
        column1_layout.addWidget(title_non_planned)
        column1_layout.addWidget(self.tableNotPlanned)
        column1_layout.addStretch()
        column1_layout.addWidget(self.chk1Button)

        column2_layout.addWidget(self.empty_hight)
        column2_layout.addWidget(title_first_start)
        column2_layout.addWidget(self.field_first_start)
        column2_layout.addSpacing(200)
        column2_layout.addWidget(self.moveButton)
        column2_layout.addStretch()

        #        layout.addWidget(self.status)

        new_blocklag_layout.addWidget(self.field_block)
        new_blocklag_layout.addWidget(self.field_lag)
        new_blocklag_layout.addWidget(self.field_gap)

#        new_blocklag_layout.addWidget(self.addBlockButton)

        column3_layout.addWidget(self.empty_hight)
        column3_layout.addWidget(title_block_lag)
        column3_layout.addLayout(new_blocklag_layout)
#        column3_layout.addWidget(self.field_block)
#        column3_layout.addWidget(self.field_lag)
        column3_layout.addWidget(self.addBlockButton)
        column3_layout.addWidget(self.tableBlockLag)
        column3_layout.addStretch()

        column4_layout.addWidget(self.empty_hight)
        column4_layout.addWidget(title_class_start)
        column4_layout.addWidget(self.tableClassStart)
        column4_layout.addStretch()
        column4_layout.addWidget(self.drawButton)
        column4_layout.addWidget(self.chk2Button)

        main_layout.addLayout(column1_layout)
        main_layout.addLayout(column2_layout)
        main_layout.addLayout(column3_layout)
        main_layout.addLayout(column4_layout)

        self.setLayout(main_layout)

    def refresh_first_start(self, raceid):
        print("refresh_first_start")
        self.raceID = raceid
        print("raceId", self.raceID)
        rows0, columns0 = queries.read_race(self.raceId)
        race = rows0[0]
        print("race", race)
        self.race_name = race[1]
        self.race_date_db: QDateEdit = race[2]
        self.race_date_str = race[2].isoformat()
        self.race_start_time_db = race[3]
        print("race", self.race_name)
        print("race_start_time_db", self.race_start_time_db)
        if self.race_start_time_db:
            self.q_time = QTime(self.race_start_time_db.hour, self.race_start_time_db.minute,
                                self.race_start_time_db.second)
        else: self.q_time = QTime(0,0)

#        print(self.q_time)

    #        self.tableBlockLag.selectionModel().selectionChanged.connect(self.upd_filter_table_cl_st)

    def populate_table(self, table, columns: list[any], rows):
        print("populate_table")
        table.clearContents()
        is_sorted = table.isSortingEnabled()
        if is_sorted: table.setSortingEnabled(False)
        table.setColumnCount(len(columns))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(columns)
        print("populate_table 2")
        for row_idx, row_data in enumerate(rows):
#            print("row_idx : ", row_idx)
            for col_idx, value in enumerate(row_data):
#                print("col_idx : ", col_idx)
                print(str(value))
                item = QTableWidgetItem("") if value is None else QTableWidgetItem(str(value))
                if isinstance(value, (int, float)) or columns[col_idx] in ("Starttid", "Nestetid"):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row_idx, col_idx, QTableWidgetItem(item))
        if is_sorted: table.setSortingEnabled(True)

    def keep_selection_colour(tabell):
        palett = tabell.palette()
#        dark_blue = QColor(0, 120, 215)  # Windows 10 blå
#        dark_blue = QColor(173, 216, 230)  # Windows 10 blå
        dark_blue = QColor(70, 130, 180)  # Windows 10 blå
        palett.setColor(QPalette.Active, QPalette.Highlight, dark_blue)
        palett.setColor(QPalette.Inactive, QPalette.Highlight, dark_blue)

        hvit = QColor(Qt.white)
        palett.setColor(QPalette.Active, QPalette.HighlightedText, hvit)
        palett.setColor(QPalette.Inactive, QPalette.HighlightedText, hvit)
        tabell.setPalette(palett)

    def first_start_edited(self):
        print("first_start_edited")
        # Update first start-time, the rebuild redundant in class_starts, and reread.
        first_time = self.field_first_start.time().toString("HH:mm:ss")
        print("first_start_edited", first_time)
        print("first_start_edited", self.race_date_str)
        self.str_new_first_start = self.race_date_str + " " + first_time

        print("first_start_edited", self.str_new_first_start)
        control.first_start_edited(self.raceId, self.str_new_first_start)
        print("first_start_edited edit ok")
        control.refresh_table(self, self.tableClassStart)
        control.refresh_table(self, self.tableBlockLag)

    def not_planned_menu(self, pos):
        rad_index = self.tableNotPlanned.rowAt(pos.y())
        if rad_index < 0:
            print("Ingen rad under musepeker – meny avbrytes")
            return

        meny = QMenu(self)

        skjul_rader = QAction("Skjul valgte rader.", self)
        skjul_rader.triggered.connect(lambda: self.skjul_valgte_rader())
        meny.addAction(skjul_rader)

        vis_skjulte = QAction("Vis skjulte rader igjen.", self)
        vis_skjulte.triggered.connect(lambda: self.vis_skjulte_rader())
        meny.addAction(vis_skjulte)

        meny.exec_(self.tableNotPlanned.viewport().mapToGlobal(pos))


    def class_start_menu(self, pos):
        rad_index = self.tableClassStart.rowAt(pos.y())
        if rad_index < 0:
            print("Ingen rad under musepeker – meny avbrytes")
            return

        meny = QMenu(self)

        slett_rad = QAction("Slett rad", self)
        slett_rad.triggered.connect(lambda: self.slett_class_start_rad(rad_index))

        slett_rader_i_båsslep = QAction("Slett bås/slep seksjon", self)
        slett_rader_i_båsslep.triggered.connect(lambda: self.slett_class_start_bås_slep(rad_index))

# Andre funksjoner: Slett hele bås/slep seksjonen, slett alt, fyttNed, flyttOpp.

#        flytt_ned = QAction("Flytt ned", self)
#        flytt_ned.triggered.connect(lambda: self.flytt_class_start_ned())

#        flytt_opp = QAction("Flytt opp", self)
#        flytt_opp.triggered.connect(lambda: self.flytt_class_start_opp())

        meny.addAction(slett_rad)
        meny.addAction(slett_rader_i_båsslep)
#        meny.addAction(flytt_ned)
#        meny.addAction(flytt_opp)

        meny.exec_(self.tableClassStart.viewport().mapToGlobal(pos))

    def block_lag_menu(self, pos):
        rad_index = self.tableBlockLag.rowAt(pos.y())
        if rad_index < 0:
            print("Ingen rad under musepeker – meny avbrytes")
            return

        meny = QMenu(self)

        slett_rad = QAction("Slett rad", self)
        slett_rad.triggered.connect(lambda: self.slett_blocklag_rad(rad_index))

        meny.addAction(slett_rad)

        meny.exec_(self.tableBlockLag.viewport().mapToGlobal(pos))


    def slett_blocklag_rad(self, rad_index):
        blocklagid = self.tableBlockLag.model().index(rad_index, 0).data()
        blockid = self.tableBlockLag.model().index(rad_index, 1).data()
        block = self.tableBlockLag.model().index(rad_index, 2).data()
        lag = self.tableBlockLag.model().index(rad_index, 3).data()

        print("Slett = " + block + ", " + str(lag) + ", " + str(blockid) + ", " + str(blocklagid))

        returned = control.delete_blocklag(self.raceId, blocklagid, blockid)
        if returned:
            self.vis_brukermelding(returned)
        else:
            control.refresh_table(self, self.tableBlockLag)
            # Refarge valgbare
            self.tableClassStart.oppdater_filter()


    def vis_brukermelding(self, tekst):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Feil")
        msg.setText(tekst)
        msg.exec_()

    def slett_class_start_rad(self, rad_index):
        classstartid = self.tableClassStart.model().index(rad_index, 0).data()
        blocklagid = self.tableClassStart.model().index(rad_index, 1).data()
        klasse = self.tableClassStart.model().index(rad_index, 4).data()

        print("Slett rad med klasse = " + klasse)

        control.delete_class_start_row(self.raceId, classstartid)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    #
    # Slett classStart rader som tilhører valgt bås/slep
    #
    def slett_class_start_bås_slep(self, rad_index):
        classstartid = self.tableClassStart.model().index(rad_index, 0).data()
        blocklagid = self.tableClassStart.model().index(rad_index, 1).data()
        klasse = self.tableClassStart.model().index(rad_index, 4).data()

        control.delete_class_start_rows(self.raceId, blocklagid)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    def skjul_valgte_rader(self):
#        print("skjul_valgte_rader start")
        model_indexes = self.tableNotPlanned.selectionModel().selectedRows()
#        print("skjul_valgte_rader 2")

        classids = set()
        for indeks in model_indexes:
            rad = indeks.row()
            classid = self.tableNotPlanned.item(rad, 0)
            classids.add(classid.text())
        print(f"classids = " + str(classids))
        control.insert_class_start_nots(self.raceId, classids)
        # Refresh
        control.refresh_table(self, self.tableNotPlanned)

    def vis_skjulte_rader(self):
        print("vis_skjulte_rader start")
        control.delete_class_start_not(self.raceId)
        # Refresh
        control.refresh_table(self, self.tableNotPlanned)


    def flytt_class_start_ned(self):
        item = self.currentItem()
        if item:
            print("flytt rad = " + item.text())
#            tekst = item.text()
#            QApplication.clipboard().setText(tekst)

    def add_block_lag(self):
#        print("skjul_valgte_rader start")
        model_indexes = self.tableBlockLag.selectionModel().selectedRows()
        if model_indexes:
            rad = model_indexes[0].row()
            blockid = self.tableBlockLag.item(rad, 1).text()
            print("Valgt rad:", rad)
            lag = self.field_lag.text()
            gap = self.field_gap.text()
            try:
                control.add_lag(blockid, lag, gap)
            except MyCustomError as e:
                self.vis_brukermelding(e.message)
        else:
            print("No rad found")
            block = self.field_block.text()
            if not block:
                self.vis_brukermelding("Du må fylle inn navnet på båsen, \neller velge en rad fra tabellen under!")
                return
            lag = self.field_lag.text()
            gap = self.field_gap.text()
            try:
                control.add_block_lag(self.raceId, block, lag, gap)
            except MyCustomError as e:
                self.vis_brukermelding(e.message)
        # Refresh
        control.refresh_table(self, self.tableBlockLag)

    def move_class_to_plan(self):
        selected_model_rows = self.tableNotPlanned.selectionModel().selectedRows()
        if not selected_model_rows:
            self.vis_brukermelding("Du må velge ei klasse å flytte Trekkeplanen!")
            return
        elif (selected_model_rows.__len__() > 9):
            self.vis_brukermelding("Du kan ikke flytte flere enn 9 klasser til Trekkeplanen samtidig!")
            return

        # Bås/slep
        block_lag_rows = self.tableBlockLag.selectionModel().selectedRows()
        if not block_lag_rows:
            self.vis_brukermelding("Du må velge et bås/tidsslep-seksjon å flytte til!")
            return

        # Hvilken bås/slep skal klassen inn i?
        row_id = block_lag_rows[0].row()
        blocklag_id = int(self.tableBlockLag.item(row_id, 0).text())
        gap = int(self.tableBlockLag.item(row_id, 4).text())
        print("gap", gap)

        # Valgt rad styrer hvor i bås/slep-seksjonen den skal inn.
        class_start_rows = self.tableClassStart.selectionModel().selectedRows()
        sort_value = 1000 # Hvis ingen rad er valgt, legges den til sist i gruppen.
        if class_start_rows:
            # En rad valgt. Ta plassen til denne, og skyv de andre lenger ned.
            row_id = class_start_rows[0].row()
            sort_value = int(self.tableClassStart.item(row_id, 4).text())
            sort_value = sort_value-10 # Plass til 9 før denne.
        # Radene er sortert i den rekkefølgen de ble selektert.
        # Men vi ønsker de sortert som den visuelle sorteringen i bildet.
        sorted_selected = sorted(selected_model_rows, key=lambda index: index.row())
        for view_index in sorted_selected:
            model_index = self.tableNotPlanned.model().index(view_index.row(), 0)
            classid = self.tableNotPlanned.model().data(model_index)
            sort_value = sort_value+1
            print("INSERT: ", classid, blocklag_id, sort_value)
            control.insert_class_start(self.raceId, blocklag_id, classid, gap, sort_value)

        # Oppdater redundante kolonner og oppfrisk tabellene.
        queries.rebuild_class_starts(self.raceId)
        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Hent verdi fra DB.
        neste = control.read_blocklag_neste(self, blocklag_id)
        # Finn item og oppdater det med verdien fra basen.
        self.set_nexttime_on_blocklag(blocklag_id, neste)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    def set_nexttime_on_blocklag(self, blocklag_id: int, neste):
        row_idx = self.get_row_idx(self.tableBlockLag, 0, blocklag_id)
        print("blocklag_id = ", blocklag_id)
        print("row_idx = ", row_idx)
        item = self.tableBlockLag.item(row_idx, 5)
        print("move_class_to_plan 2", item)
        item.setText(str(neste))
        print("move_class_to_plan 3")

    def get_row_idx(self, table: QTableWidget, col_idx: int, col_value):
        print("get_row_idx", col_idx, col_value)
        for row_idx in range(table.rowCount()):
            item = int(table.item(row_idx, col_idx).text())
#            print("item", item)
            if item == col_value:
                return row_idx
        return None

    def select_race(self: QWidget):
        print("select_race")
        dialog = SelectRaceDialog([])
        print("select_race 2")
        control.refresh_raise_list(self, dialog)
        print("select_race 3")

        #        dialog = VelgLøpDialog([(101, "Løp 1"), (102, "Løp 2"), (103, "Finale")])
        if dialog.exec_() == QDialog.Accepted:
            valgt_id = dialog.valgt_løpsid
            print("Brukeren valgte løps-ID:", valgt_id)

            self.raceId = valgt_id
            control.refresh_table(self, self.tableNotPlanned)
            control.refresh_table(self, self.tableBlockLag)
            control.refresh_table(self, self.tableClassStart)
            print("refresh 2", self.raceId)

            self.refresh_first_start(self.raceId)
            print("q_time", self.q_time)
#            self.q_time.setText(str(self.q_time.text()))
            print("select_race 4")
            self.field_first_start.setTime(self.q_time)
            print("select_race 6")
            self.setWindowTitle("Brikkesys Trekkeplan - " + self.race_name + "   " + self.race_date_str )

        else:
            print("Brukeren avbrøt")

    def sett_redigerbare_kolonner(self, table, redigerbare_kolonner: list[int]):
        for rad in range(table.rowCount()):
            for kol in range(table.columnCount()):
                item = table.item(rad, kol)
                if item is None:
                    item = QTableWidgetItem()
                    table.setItem(rad, kol, item)

                if kol in redigerbare_kolonner:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
