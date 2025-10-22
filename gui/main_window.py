from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, \
     QTimeEdit, QMenu, QAction, QMessageBox, QLineEdit, QDialog, QDateEdit, QSpacerItem, QSizePolicy, QFrame
from PyQt5.QtCore import Qt, QTime, QSettings, QUrl, QTimer
from PyQt5.QtGui import QPalette, QColor, QIntValidator, QIcon, QDesktopServices

from control import control
from control.errors import MyCustomError
from db import queries
from db.connection import ConnectionManager
from gui.about_dialog import AboutDialog

from gui.filtered_table import FilteredTable
from gui.split_club_mates import SplitClubMates
from gui.velg_løp_dialog import SelectRaceDialog


class MainWindow(QWidget):
    def __init__(self, config, conn_mgr, icon_path, pdf_path):
        super().__init__()
        self.icon_path = icon_path
        self.pdf_path = pdf_path
        self.config = config
        self.conn_mgr: ConnectionManager = conn_mgr
        self.col_widths_not_planned = [0, 120, 50, 100, 60]
        self.col_widths_block_lag = [0, 0, 100, 50, 50, 70]
        self.col_widths_class_start = [0, 0, 100, 50, 0, 100, 100, 60, 50, 60, 60, 60, 70, 70]

        self.raceId = self.hent_raceid()
        self.str_new_first_start = None
#        self.resize(1677, 780)
        self.resize(1497, 780)
        self.move(0, 0)

        self.log = True
        self.race_name = None
        self.q_time = None
        #
        # Komponenter
        #
#        self.status = QLabel("Status: Ikke tilkoblet")
        self.style_table_header = "font-weight: bold; font-size: 16px; margin: 10px 0;"
        title_non_planned = QLabel("Ikke-planlagte klasser")
        title_non_planned.setStyleSheet(self.style_table_header)
        title_block_lag = QLabel("Bås/tidsslep/gap")
        title_block_lag.setStyleSheet(self.style_table_header)
        title_class_start = QLabel("Trekkeplan")
        title_class_start.setStyleSheet(self.style_table_header)

        title_first_start = QLabel("Første start:")
        title_first_start.setStyleSheet(self.style_table_header)
        self.field_first_start = QTimeEdit()
        self.field_first_start.setDisplayFormat("HH:mm")
        self.field_first_start.setFixedWidth(70)
        self.field_block = QLineEdit()
        self.field_block.setReadOnly(False)
        self.field_block.setFixedWidth(100)
        self.field_lag = QLineEdit()
        self.field_lag.setReadOnly(False)
        self.field_lag.setFixedWidth(50)
        self.field_lag.setValidator(QIntValidator(0, 999))
        self.field_lag.setText("0")
        self.field_gap = QLineEdit()
        self.field_gap.setReadOnly(False)
        self.field_gap.setFixedWidth(50)
        self.field_gap.setValidator(QIntValidator(0, 999))
        self.field_gap.setText("60")

        self.tableNotPlanned = QTableWidget()
        self.tableNotPlanned.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableNotPlanned.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableNotPlanned.verticalHeader().setVisible(False)
        self.tableNotPlanned.setSortingEnabled(True)
        self.tableNotPlanned.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableNotPlanned.customContextMenuRequested.connect(self.not_planned_menu)
        # Og på header.
        self.tableNotPlanned.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableNotPlanned.horizontalHeader().customContextMenuRequested.connect(self.not_planned_header_menu)

        self.tableBlockLag = QTableWidget()
        self.tableBlockLag.setEditTriggers(QTableWidget.NoEditTriggers)
#        self.tableBlockLag.setMinimumSize(210, 100)
#        self.tableBlockLag.setMaximumSize(210, 2000)
        self.tableBlockLag.setSelectionMode(QTableWidget.SingleSelection)
        self.tableBlockLag.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBlockLag.verticalHeader().setVisible(False)
        self.tableBlockLag.setSortingEnabled(True)
        self.tableBlockLag.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableBlockLag.customContextMenuRequested.connect(self.block_lag_menu)

        self.tableClassStart = FilteredTable(self.tableBlockLag, 0, 1)  #QTableWidget()
#        self.tableClassStart.setMinimumSize(660, 100)
#        self.tableClassStart.setMaximumSize(660, 2000)
        self.tableClassStart.setSelectionMode(QTableWidget.SingleSelection)
        self.tableClassStart.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableClassStart.verticalHeader().setVisible(False)
        self.tableClassStart.setSortingEnabled(False)
        self.tableClassStart.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableClassStart.customContextMenuRequested.connect(self.class_start_menu)

        self.hjelp_knapp = QPushButton("Hjelp")
        self.hjelp_knapp.setFixedWidth(150)
        self.hjelp_knapp.clicked.connect(self.vis_hjelp)

        layout = QVBoxLayout()
        self.aboutButton = QPushButton("Om Trekkeplan")
        self.aboutButton.setFixedWidth(150)
#        self.aboutButton.setToolTip("Velg et annet løp.")
        self.aboutButton.clicked.connect(self.vis_about_dialog)
        layout.addWidget(self.aboutButton)
        central = QWidget()
        central.setLayout(layout)
#        self.setCentralWidget(central)

        self.raceButton = QPushButton("Velg løp")
        self.raceButton.setFixedWidth(150)
        self.raceButton.setToolTip("Velg et annet løp.")
        self.raceButton.clicked.connect(self.select_race)

        self.moveButton = QPushButton("==>")
        self.moveButton.setFixedWidth(100)
        self.moveButton.setToolTip("Flytt valgte klasser over til Trekkeplan, i den gruppen du har valgt (bås/ slep.")
        self.moveButton.clicked.connect(self.move_class_to_plan)

        self.addBlockButton = QPushButton("+")
        self.addBlockButton.setFixedWidth(157)
        self.addBlockButton.setToolTip("Legg til en ny bås/slep med vedier fra feltene over.\nHvis du har valgt ut en rad i tabellen under,\nvil bås feltet bli hentet herfra.")
        self.addBlockButton.clicked.connect(self.add_block_lag)

        self.buttonDrawStartTimes = QPushButton("Trekk starttider")
        self.buttonDrawStartTimes.setFixedWidth(150)
        self.buttonDrawStartTimes.setToolTip("Trekk starttider for alle klasser i trekkeplanen.")
        self.buttonDrawStartTimes.clicked.connect(self.draw_start_times)

        self.buttonClearStartTimes = QPushButton("Fjern starttider")
        self.buttonClearStartTimes.setFixedWidth(150)
        self.buttonClearStartTimes.setToolTip("Fjern starttider for alle klasser i trekkeplanen.")
        self.buttonClearStartTimes.clicked.connect(self.clear_start_times)

        self.buttonClubMates = QPushButton("Splitt klubbkamerater")
        self.buttonClubMates.setFixedWidth(250)
        self.buttonClubMates.setToolTip("Løpere fra samme klubb som starter etter hverandre i samme klasse.")
        self.buttonClubMates.clicked.connect(self.handle_club_mates)

        self.startListButton = QPushButton("Startliste")
        self.startListButton.setFixedWidth(150)
        self.startListButton.setToolTip("Lag startliste pr. klasse.")
        self.startListButton.clicked.connect(self.make_startlist)

        self.starterListButton = QPushButton("Starter-liste")
        self.starterListButton.setFixedWidth(150)
        self.starterListButton.setToolTip("Lag startliste pr. starttid.")
        self.starterListButton.clicked.connect(self.make_starterlist)

        self.make_layout(title_block_lag, title_class_start, title_first_start, title_non_planned)

        #        self.load_button.clicked.connect(self.load_data)
        #
        # Les fra MySQL initielt.
        #
        if self.log: print("refresh 1", self.raceId)
        self.refresh_first_start(self.raceId)
#        print("refresh 1 ferdig")

#        self.setWindowTitle(self.race_name + "   " + self.race_date_str + "             Trekkeplan")
        if not self.race_name: self.setWindowTitle("Brikkesys/SvR Trekkeplan - ")
        else: self.setWindowTitle("Brikkesys/SvR Trekkeplan - " + self.race_name + "   " + self.race_date_str )



        self.setWindowIcon(QIcon(self.icon_path))

        self.field_first_start.editingFinished.connect(self.first_start_edited)
        if self.q_time: self.field_first_start.setTime(self.q_time)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableBlockLag)
        control.refresh_table(self, self.tableClassStart)

        self.tableNotPlanned.setColumnHidden(0, True)
        self.tableNotPlanned.sortItems(1, order=Qt.AscendingOrder)

        self.tableBlockLag.setColumnHidden(0, True)
        self.tableBlockLag.setColumnHidden(1, True)
        self.tableBlockLag.sortItems(2, order=Qt.AscendingOrder)

        self.tableClassStart.setColumnHidden(0, True)
        self.tableClassStart.setColumnHidden(1, True)
        self.tableClassStart.setColumnHidden(4, True) # Sortorder

        self.tableClassStart.itemChanged.connect(self.classStart_item_changed)

#        self.print_col_width(self.tableNotPlanned)
#        self.print_col_width(self.tableBlockLag)
#        self.print_col_width(self.tableClassStart)

        # Behold samme farge når tabell ikke er i fokus.
        self.keep_selection_colour(self)
        #        self.keep_selection_colour(self.tableBlockLag)
        #        self.keep_selection_colour(self.tableClassStart)


    def make_layout(self, title_block_lag: QLabel | QLabel, title_class_start: QLabel | QLabel,
                    title_first_start: QLabel | QLabel, title_non_planned: QLabel | QLabel):
        #
        # Layout
        #
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        center_ramme = QFrame()
        center_ramme.setFrameShape(QFrame.StyledPanel)
        center_ramme.setFrameShadow(QFrame.Plain)
        center_ramme.setLayout(center_layout)
        bottom_ramme = QFrame()
        bottom_ramme.setFrameShape(QFrame.StyledPanel)
        bottom_ramme.setFrameShadow(QFrame.Plain)
        bottom_ramme.setLayout(bottom_layout)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(center_ramme)
        main_layout.addWidget(bottom_ramme)

        top_layout.addWidget(self.raceButton)
        top_layout.addWidget(self.hjelp_knapp)
        top_layout.addWidget(self.aboutButton)
        top_layout.addWidget(title_first_start)
        top_layout.addWidget(self.field_first_start)
        top_layout.addStretch()

        column1_layout = QVBoxLayout()
#        column2_layout = QVBoxLayout()
        new_blocklag_layout = QHBoxLayout()
        column3_layout = QVBoxLayout()
        column4_layout = QVBoxLayout()
#        button_layout = QHBoxLayout()

        column1_layout.addWidget(title_non_planned)
        column1_layout.addWidget(self.tableNotPlanned)
        column1_layout.addStretch()

#        column2_layout.addWidget(title_first_start)
#        column2_layout.addWidget(self.field_first_start)
#        column2_layout.addSpacing(200)
#        column2_layout.addWidget(self.moveButton)
#        column2_layout.addStretch()

        new_blocklag_layout.addWidget(self.field_block)
        new_blocklag_layout.addWidget(self.field_lag)
        new_blocklag_layout.addWidget(self.field_gap)
        new_blocklag_layout.addStretch()

        column3_layout.addWidget(title_block_lag)
        column3_layout.addLayout(new_blocklag_layout)
        column3_layout.addWidget(self.addBlockButton)
        column3_layout.addWidget(self.tableBlockLag)
#        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
#        column3_layout.addItem(spacer)
        column3_layout.addStretch()

        bottom_layout.addWidget(self.startListButton)
        bottom_layout.addWidget(self.starterListButton)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.buttonClubMates)
        bottom_layout.addWidget(self.buttonClearStartTimes)
        bottom_layout.addWidget(self.buttonDrawStartTimes)

        header_class_start_layout = QHBoxLayout()
        header_class_start_layout.addWidget(self.moveButton)
        header_class_start_layout.addWidget(title_class_start)

        column4_layout.addLayout(header_class_start_layout)
        column4_layout.addWidget(self.tableClassStart)
        column4_layout.addStretch()

        center_layout.addLayout(column1_layout)
#        center_layout.addLayout(column2_layout)
        center_layout.addLayout(column3_layout)
        center_layout.addLayout(column4_layout)

#        bottom_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def refresh_first_start(self, raceid):
        if self.log: print("refresh_first_start")
#        self.raceID = raceid
#        print("raceId", self.raceID)
        rows0, columns0 = queries.read_race(self.conn_mgr, self.raceId)
        if not rows0: return
        race = rows0[0]
#        print("race", race)
        self.race_name = race[1]
        self.race_date_db: QDateEdit = race[2]
        self.race_date_str = race[2].isoformat()
        self.race_start_time_db = race[3]
#        print("race", self.race_name)
#        print("race_start_time_db", self.race_start_time_db)
        if self.race_start_time_db:
            self.q_time = QTime(self.race_start_time_db.hour, self.race_start_time_db.minute,
                                self.race_start_time_db.second)
        else: self.q_time = QTime(0,0)

#        print(self.q_time)

    #        self.tableBlockLag.selectionModel().selectionChanged.connect(self.upd_filter_table_cl_st)

    def populate_table(self, table, columns: list[any], rows):
        if self.log: print("populate_table")
        self.tableClassStart.blockSignals(True)
#        print("populate_table 2")
        table.clearContents()
        is_sorted = table.isSortingEnabled()
        if is_sorted: table.setSortingEnabled(False)
        table.setColumnCount(len(columns))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(columns)
#        print("populate_table 3")
        for row_idx, row_data in enumerate(rows):
#            print("row_idx : ", row_idx)
            for col_idx, value in enumerate(row_data):
#                print("col_idx : ", col_idx)
#                print(str(value))
                item = QTableWidgetItem("") if value is None else QTableWidgetItem(str(value))
                if isinstance(value, (int, float)) or columns[col_idx] in ("Starttid", "Nestetid"):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row_idx, col_idx, QTableWidgetItem(item))
        if is_sorted: table.setSortingEnabled(True)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.tableClassStart.blockSignals(False)
        if self.log: print("populate_table end")

    def keep_selection_colour(self, table):
        if self.log: print("keep_selection_colour")
        palett = table.palette()
#        dark_blue = QColor(0, 120, 215)  # Windows 10 blå
#        dark_blue = QColor(173, 216, 230)  # Windows 10 blå
        dark_blue = QColor(70, 130, 180)  # Windows 10 blå
        palett.setColor(QPalette.Active, QPalette.Highlight, dark_blue)
        palett.setColor(QPalette.Inactive, QPalette.Highlight, dark_blue)

        hvit = QColor(Qt.white)
        palett.setColor(QPalette.Active, QPalette.HighlightedText, hvit)
        palett.setColor(QPalette.Inactive, QPalette.HighlightedText, hvit)
        table.setPalette(palett)

    def first_start_edited(self):
        if self.log: print("first_start_edited")
        # Update first start-time, the rebuild redundant in class_starts, and reread.
        first_time = self.field_first_start.time().toString("HH:mm:ss")
#        print("first_start_edited", first_time)
#        print("first_start_edited", self.race_date_str)
        self.str_new_first_start = self.race_date_str + " " + first_time

#        print("first_start_edited", self.str_new_first_start)
        control.first_start_edited(self, self.raceId, self.str_new_first_start)
#        print("first_start_edited edit ok")
        control.refresh_table(self, self.tableClassStart)
        control.refresh_table(self, self.tableBlockLag)

    def not_planned_menu(self, pos):
        if self.log: print("not_planned_menu")
        rad_index = self.tableNotPlanned.rowAt(pos.y())
        print("rad_index", rad_index)
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

    def not_planned_header_menu(self, pos):
        if self.log: print("not_planned_header_menu")
        # Høyreklikk på kolonneheader
        meny = QMenu(self)
        vis_skjulte = QAction("Vis skjulte rader igjen.", self)
        vis_skjulte.triggered.connect(lambda: self.vis_skjulte_rader())
        meny.addAction(vis_skjulte)

        meny.exec_(self.tableNotPlanned.viewport().mapToGlobal(pos))

        meny = QMenu(self)

        vis_skjulte = QAction("Vis skjulte rader igjen.", self)
        vis_skjulte.triggered.connect(lambda: self.vis_skjulte_rader())
        meny.addAction(vis_skjulte)

        meny.exec_(self.tableNotPlanned.viewport().mapToGlobal(pos))


    def class_start_menu(self, pos):
        if self.log: print("class_start_menu")
        rad_index = self.tableClassStart.rowAt(pos.y())
        print("rad_index", rad_index)
        if rad_index < 0:
            print("Ingen rad under musepeker – meny avbrytes")
            return

        selected_indexes = self.tableClassStart.selectionModel().selectedRows()
        if selected_indexes:
            row_inx = selected_indexes[0].row()
            if row_inx == rad_index:
                meny = QMenu(self)

                slett_rad = QAction("Slett rad", self)
                slett_rad.triggered.connect(lambda: self.slett_class_start_rad(rad_index))

                slett_rader_i_båsslep = QAction("Slett bås/slep seksjon", self)
                slett_rader_i_båsslep.triggered.connect(lambda: self.slett_class_start_bås_slep(rad_index))

                slett_rader_alle = QAction("Slett alle", self)
                slett_rader_alle.triggered.connect(lambda: self.slett_class_start_alle())

                meny.addAction(slett_rad)
                meny.addAction(slett_rader_i_båsslep)
                meny.addAction(slett_rader_alle)
                #        meny.addAction(flytt_ned)
                #        meny.addAction(flytt_opp)

                meny.exec_(self.tableClassStart.viewport().mapToGlobal(pos))

# Andre funksjoner: slett alt, fyttNed, flyttOpp.

#        flytt_ned = QAction("Flytt ned", self)
#        flytt_ned.triggered.connect(lambda: self.flytt_class_start_ned())

#        flytt_opp = QAction("Flytt opp", self)
#        flytt_opp.triggered.connect(lambda: self.flytt_class_start_opp())


    def block_lag_menu(self, pos):
        if self.log: print("block_lag_menu")
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
        if self.log: print("slett_blocklag_rad")
        blocklagid = self.tableBlockLag.model().index(rad_index, 0).data()
        blockid = self.tableBlockLag.model().index(rad_index, 1).data()
        block = self.tableBlockLag.model().index(rad_index, 2).data()
        lag = self.tableBlockLag.model().index(rad_index, 3).data()

#        print("Slett = " + block + ", " + str(lag) + ", " + str(blockid) + ", " + str(blocklagid))

        returned = control.delete_blocklag(self, self.raceId, blocklagid, blockid)
        if returned:
            self.vis_brukermelding(returned)
        else:
            control.refresh_table(self, self.tableBlockLag)
            # Refarge valgbare
            self.tableClassStart.oppdater_filter()


    def vis_brukermelding(self, tekst):
        if self.log: print("vis_brukermelding")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Feil")
        msg.setText(tekst)
        msg.exec_()

    def slett_class_start_rad(self, rad_index):
        if self.log: print("slett_class_start_rad")
        classstartid = self.tableClassStart.model().index(rad_index, 0).data()
        blocklagid = self.tableClassStart.model().index(rad_index, 1).data()
        klasse = self.tableClassStart.model().index(rad_index, 4).data()

#        print("Slett rad med klasse = " + klasse)

        control.delete_class_start_row(self, self.raceId, classstartid)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    #
    # Slett classStart rader som tilhører valgt bås/slep
    #
    def slett_class_start_bås_slep(self, rad_index):
        if self.log: print("slett_class_start_bås_slep")
        classstartid = self.tableClassStart.model().index(rad_index, 0).data()
        blocklagid = self.tableClassStart.model().index(rad_index, 1).data()
        klasse = self.tableClassStart.model().index(rad_index, 4).data()

        control.delete_class_start_rows(self, self.raceId, blocklagid)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    #
    # Slett alle classStart rader for dette løpet.
    #
    def slett_class_start_alle(self):
        if self.log: print("slett_class_start_alle")
        control.delete_class_start_all(self, self.raceId)

        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)


    def skjul_valgte_rader(self):
        if self.log: print("skjul_valgte_rader")
        model_indexes = self.tableNotPlanned.selectionModel().selectedRows()
#        print("skjul_valgte_rader 2")

        classids = set()
        for indeks in model_indexes:
            rad = indeks.row()
            classid = self.tableNotPlanned.item(rad, 0)
            classids.add(classid.text())
#        print(f"classids = " + str(classids))
        control.insert_class_start_nots(self, self.raceId, classids)
        # Refresh
        control.refresh_table(self, self.tableNotPlanned)

    def vis_skjulte_rader(self):
        if self.log: print("vis_skjulte_rader")
        control.delete_class_start_not(self, self.raceId)
        # Refresh
        control.refresh_table(self, self.tableNotPlanned)


    def flytt_class_start_ned(self):
        if self.log: print("flytt_class_start_ned")
        item = self.currentItem()
        if item:
            print("flytt rad = " + item.text())
#            tekst = item.text()
#            QApplication.clipboard().setText(tekst)

    def add_block_lag(self):
        if self.log: print("add_block_lag")
        if self.raceId == 0:
            self.vis_brukermelding("Må velge et løp først!")
            return
        model_indexes = self.tableBlockLag.selectionModel().selectedRows()
        if model_indexes:
            rad = model_indexes[0].row()
            blockid = self.tableBlockLag.item(rad, 1).text()
#            print("Valgt rad:", rad)
            lag = self.field_lag.text()
            gap = self.field_gap.text()
            try:
                control.add_lag(self, blockid, lag, gap)
            except MyCustomError as e:
                self.vis_brukermelding(e.message)
        else:
#            print("No rad found")
            block = self.field_block.text()
            if not block:
                self.vis_brukermelding("Du må fylle inn navnet på båsen, \neller velge en rad fra tabellen under!")
                return
            lag = self.field_lag.text()
            if not lag: lag = 0
            gap = self.field_gap.text()
            if not gap: gap = 0
            try:
                control.add_block_lag(self, self.raceId, block, lag, gap)
            except MyCustomError as e:
                self.vis_brukermelding(e.message)
        # Refresh
        control.refresh_table(self, self.tableBlockLag)

    def move_class_to_plan(self):
        if self.log: print("move_class_to_plan")
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
#        print("gap", gap)

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
#            print("INSERT: ", classid, blocklag_id, sort_value)
            control.insert_class_start(self, self.raceId, blocklag_id, classid, gap, sort_value)

        # Oppdater redundante kolonner og oppfrisk tabellene.
        queries.rebuild_class_starts(self.conn_mgr, self.raceId)
        control.refresh_table(self, self.tableNotPlanned)
        control.refresh_table(self, self.tableClassStart)

        # Hent verdi fra DB.
        neste = control.read_blocklag_neste(self, blocklag_id)
        # Finn item og oppdater det med verdien fra basen.
        self.set_nexttime_on_blocklag(blocklag_id, neste)

        # Refarge valgbare
        self.tableClassStart.oppdater_filter()

    def set_nexttime_on_blocklag(self, blocklag_id: int, neste):
        if self.log: print("set_nexttime_on_blocklag")
        self.tableClassStart.blockSignals(True)
        row_idx = self.get_row_idx(self.tableBlockLag, 0, blocklag_id)
#        print("blocklag_id = ", blocklag_id)
#        print("row_idx = ", row_idx)
        item = self.tableBlockLag.item(row_idx, 5)
        print("neste", neste)
        item.setText(str(neste))
        self.tableClassStart.blockSignals(False)

#        print("move_class_to_plan 3")

    def get_row_idx(self, table: QTableWidget, col_idx: int, col_value):
        if self.log: print("get_row_idx")
        print("get_row_idx", col_idx, col_value)
        for row_idx in range(table.rowCount()):
            print("get_row_idx", row_idx)
            item = table.item(row_idx, col_idx).text()
#            item = int(table.item(row_idx, col_idx).text())
            print("item, col_value", item, col_value)
            if item == str(col_value):
                print("return row_idx=", row_idx)
                return row_idx
        print("System error: return row_idx=None")
        return None

    def vis_about_dialog(self):
        dialog = AboutDialog()
        dialog.setWindowIcon(QIcon(self.icon_path))
        dialog.exec_()


    def select_race(self: QWidget):
        if self.log: print("select_race")
#        dialog = SelectRaceDialog([], self)
        dialog = SelectRaceDialog(self)
        dialog.setWindowIcon(QIcon(self.icon_path))

#        control.refresh_race_list(self, dialog)
        if self.log: print("select_race 2")

        if dialog.exec_() == QDialog.Accepted:
            valgt_id = dialog.valgt_løpsid

            self.raceId = valgt_id
            control.refresh_table(self, self.tableNotPlanned)
            control.refresh_table(self, self.tableBlockLag)
            control.refresh_table(self, self.tableClassStart)

            self.refresh_first_start(self.raceId)
            self.field_first_start.setTime(self.q_time)
            self.setWindowTitle("Brikkesys/SvR Trekkeplan - " + self.race_name + "   " + self.race_date_str)
            self.lagre_raceid(self.raceId)
        else:
            print("Brukeren avbrøt")

    def handle_club_mates(self):
        if self.log: print("handle_club_mates")
        dialog = SplitClubMates(self)
        dialog.setWindowIcon(QIcon(self.icon_path))
        dialog.exec_() # modal visning.

    def print_col_width(self, table):
        for kol in range(table.columnCount()):
            bredde = table.columnWidth(kol)
            print(f"Kolonne {kol}: {bredde}px")

    def set_fixed_widths(self, table, widths):
        for col_inx, width in enumerate(widths):
            table.setColumnWidth(col_inx, width)

    def sett_redigerbare_kolonner(self, table, redigerbare_kolonner: list[int]):
        if self.log: print("sett_redigerbare_kolonner")
        self.tableClassStart.blockSignals(True)
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
        self.tableClassStart.blockSignals(False)

    def classStart_item_changed(self, item):
        if self.log: print("classStart_item_changed")
        self.tableClassStart.blockSignals(True)
        idx_col = item.column()
        idx_row = item.row()
#        if self.tableClassStart.hasFocus():
        if idx_col in [10,11]: # Antall ledige før og etter.
            new_value = item.text()
            item.setText(new_value)
            classstartid = self.tableClassStart.item(idx_row, 0).text()
            blocklagid = self.tableClassStart.item(idx_row, 1).text()
#            print(f"Endret rad {idx_row}, kol {idx_col} til: {new_value}")
#            print("classstartid", classstartid)
            if idx_col==10:
                control.class_start_free_updated(self, self.raceId, classstartid, blocklagid, new_value, 1)
            if idx_col==11:
                control.class_start_free_updated(self, self.raceId, classstartid, blocklagid, new_value, 2)

        self.tableClassStart.blockSignals(False)

    def lagre_raceid(self, raceid: int):
        settings = QSettings("Brikkesys_svr", "Trekkeplan")
        settings.setValue("Race_id", raceid)

    def hent_raceid(self) -> int | None:
        settings = QSettings("Brikkesys_svr", "Trekkeplan")
        verdi = settings.value("Race_id", None)
        return int(verdi) if verdi is not None else 0

    def juster_tabellhøyde(self, table, max_height = 600):
        if self.log: print("juster_tabellhøyde")
        header_h = table.horizontalHeader().height()
        rad_høyde = header_h
        scrollbar_h = table.horizontalScrollBar().height() if table.horizontalScrollBar().isVisible() else 0
        total_høyde = header_h + (rad_høyde * table.rowCount()) + scrollbar_h + 2  # +2 for ramme
        begrenset_høyde = min(total_høyde, max_height)
        table.setFixedHeight(begrenset_høyde)
#        print("høyder", header_h, rad_høyde, scrollbar_h, total_høyde, begrenset_høyde)

    def juster_tabell_vidde(self, tabell, ekstra_margin=2):
        if self.log: print("juster_tabell_vidde")
        total_bredde = sum(tabell.columnWidth(kol) for kol in range(tabell.columnCount()))
        vertikal_scroll = tabell.verticalScrollBar().sizeHint().width() # if tabell.verticalScrollBar().isVisible() else 0
        ramme = tabell.frameWidth() * 2
        tabell.setFixedWidth(total_bredde + vertikal_scroll + ramme + ekstra_margin)
        print("vertikal_scroll", vertikal_scroll)

    def draw_start_times(self):
        if self.log: print("draw_start_times")
        control.draw_start_times(self, self.raceId)

    def clear_start_times(self):
        if self.log: print("clear_start_times")
        control.clear_start_times(self, self.raceId)

    def make_startlist(self):
        if self.log: print("make_startlist")
        control.make_startlist(self, self.raceId)

    def make_starterlist(self):
        if self.log: print("make_starterlist")
        control.make_starterlist(self, self.raceId)

    def vis_hjelp(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.pdf_path))

    def closeEvent(self, event):
        size = self.size()
        print(f"Vinduet avsluttes med størrelse: {size.width()} x {size.height()}")
        super().closeEvent(event)

    def set_table_sizes(self, table, col_sizes):
        self.set_fixed_widths(table, col_sizes)
        table.resizeRowsToContents()
        self.juster_tabellhøyde(table)
        self.juster_tabell_vidde(table)
