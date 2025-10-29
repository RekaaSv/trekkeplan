import datetime
import logging

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTableWidget, \
    QTimeEdit, QMenu, QAction, QMessageBox, QLineEdit, QDialog, QSizePolicy, QFrame, \
    QApplication, QShortcut
from PyQt5.QtCore import Qt, QTime, QSettings, QUrl
from PyQt5.QtGui import QPalette, QColor, QIntValidator, QIcon, QDesktopServices, QKeySequence, QFont, QBrush

from control import control
from control.errors import MyCustomError
from db import queries
from db.connection import ConnectionManager
from gui.about_dialog import AboutDialog
from gui.block_line_edit import BlockLineEdit
from gui.draw_plan_table_item import DrawPlanTableItem

from gui.filtered_table import FilteredTable
from gui.split_club_mates import SplitClubMates
from gui.select_race_dialog import SelectRaceDialog


class MainWindow(QWidget):
    def __init__(self, config, conn_mgr, icon_path, pdf_path):
        super().__init__()
        self.icon_path = icon_path
        self.pdf_path = pdf_path
        self.config = config
        self.conn_mgr: ConnectionManager = conn_mgr
        self.col_widths_not_planned = [0, 120, 50, 100, 60]
        self.col_widths_block_lag = [0, 0, 100, 50, 50, 70, 70]
        self.col_widths_class_start = [0, 0, 100, 50, 0, 100, 100, 60, 50, 60, 65, 65, 70, 70]

        # Globale variable
        self.race_id = self.get_raceid_from_registry() # Lagres i registry.
        self.race_name = None

        self.button_style = """
            QPushButton {
                background-color: rgb(200, 220, 240);
                border: 1px solid #888;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgb(170, 200, 230);
            }
            QPushButton:pressed {
                background-color: rgb(150, 180, 220);
            }
        """
        field_input_style = """
        QLineEdit {
            background-color: rgb(255, 250, 205);  /* svak gul */
        }
        """

        self.resize(1497, 780)
        self.move(0, 0)

        #
        # Komponenter
        #
        self.style_table_header = "font-weight: bold; font-size: 16px; margin: 10px 0;"
        title_non_planned = QLabel("Ikke-planlagte klasser")
        title_non_planned.setStyleSheet(self.style_table_header)
        title_block_lag = QLabel("Bås/tidsslep/gap")
        title_block_lag.setStyleSheet(self.style_table_header)
        title_class_start = QLabel("Trekkeplan")
        title_class_start.setStyleSheet(self.style_table_header)

        style_sheet_time = """
            background-color: rgb(255, 250, 205);  /* svak gul */
            border: 1px solid #aaa;
            padding: 2px;
            border-radius: 3px;
        """
        title_first_start = QLabel("Første start:")
        title_first_start.setStyleSheet(self.style_table_header)
        self.field_first_start = QTimeEdit()
        self.field_first_start.setButtonSymbols(QTimeEdit.NoButtons)  # Skjuler opp/ned-piler
        self.field_first_start.setStyleSheet(style_sheet_time)

        style_sheet_time_ro = """
            background-color: rgb(255, 200, 200);
            border: 1px solid #aaa;
            padding: 2px;
            border-radius: 3px;
        """
        title_last_start = QLabel("Siste start:")
        title_last_start.setStyleSheet(self.style_table_header)
        self.field_last_start = QTimeEdit()
        self.field_last_start.setReadOnly(True)
        self.field_last_start.setButtonSymbols(QTimeEdit.NoButtons)  # Skjuler opp/ned-piler
        self.field_last_start.setStyleSheet(style_sheet_time_ro)
        self.field_last_start.setDisplayFormat("HH:mm:ss")
        self.field_last_start.setFixedWidth(80)

        title_duration = QLabel("Varighet:")
        title_duration.setStyleSheet(self.style_table_header)
        self.field_duration = QLabel()
        self.field_duration.setStyleSheet(style_sheet_time_ro)

        title_utilization = QLabel("Utnyttelse (%):")
        title_utilization.setStyleSheet(self.style_table_header)
        self.field_utilization = QLabel()
        self.field_utilization.setStyleSheet(style_sheet_time_ro)

        time_font = QFont()
        time_font.setPointSize(10)
        self.field_first_start.setFont(time_font)
        self.field_last_start.setFont(time_font)
        self.field_duration.setFont(time_font)
        self.field_duration.setFixedHeight(30)
        self.field_utilization.setFont(time_font)
        self.field_utilization.setFixedHeight(30)

        self.field_first_start.setDisplayFormat("HH:mm:ss")
        self.field_first_start.setFixedWidth(80)
        self.field_block = BlockLineEdit(self)
        self.field_block.setStyleSheet(field_input_style)
        self.field_block.setReadOnly(False)
        self.field_block.setFixedWidth(100)
        self.field_lag = QLineEdit()
        self.field_lag.setStyleSheet(field_input_style)
        self.field_lag.setReadOnly(False)
        self.field_lag.setFixedWidth(50)
        self.field_lag.setValidator(QIntValidator(0, 999))
        self.field_lag.setText("0")
        self.field_gap = QLineEdit()
        self.field_gap.setStyleSheet(field_input_style)
        self.field_gap.setReadOnly(False)
        self.field_gap.setFixedWidth(50)
        self.field_gap.setValidator(QIntValidator(0, 999))
        self.field_gap.setText("60")

        self.table_header_style_sheet = """
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333;
                font-weight: bold;
                padding: 1px;
                border: 1px solid #ccc;
            }
        """

        self.table_not_planned = QTableWidget()
        self.table_not_planned.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_not_planned.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_not_planned.verticalHeader().setVisible(False)
        self.table_not_planned.setSortingEnabled(True)
        self.table_not_planned.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_not_planned.customContextMenuRequested.connect(self.show_not_planned_menu)
        # Og på header.
        self.table_not_planned.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_not_planned.horizontalHeader().customContextMenuRequested.connect(self.show_not_planned_header_menu)
        self.table_not_planned.horizontalHeader().setStyleSheet(self.table_header_style_sheet)

        self.table_block_lag = QTableWidget()
        self.table_block_lag.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_block_lag.setSelectionMode(QTableWidget.SingleSelection)
        self.table_block_lag.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_block_lag.verticalHeader().setVisible(False)
        self.table_block_lag.setSortingEnabled(True)
        self.table_block_lag.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_block_lag.customContextMenuRequested.connect(self.show_block_lag_menu)
        self.table_block_lag.horizontalHeader().setStyleSheet(self.table_header_style_sheet)

        self.table_class_start = FilteredTable(self.table_block_lag, 0, 1)  #QTableWidget()
#        parent.table_class_start.setMinimumSize(660, 100)
#        parent.table_class_start.setMaximumSize(660, 2000)
        self.table_class_start.setSelectionMode(QTableWidget.SingleSelection)
        self.table_class_start.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_class_start.verticalHeader().setVisible(False)
        self.table_class_start.setSortingEnabled(False)
        self.table_class_start.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_class_start.customContextMenuRequested.connect(self.show_class_start_menu)
        self.table_class_start.horizontalHeader().setStyleSheet(self.table_header_style_sheet)

        self.help_button = QPushButton("Hjelp")
        self.help_button.setStyleSheet(self.button_style)
        self.help_button.setFixedWidth(150)
        self.help_button.clicked.connect(self.open_help)

        layout = QVBoxLayout()
        self.about_button = QPushButton("Om Trekkeplan")
        self.about_button.setStyleSheet(self.button_style)
        self.about_button.setFixedWidth(150)
        self.about_button.clicked.connect(self.show_about_dialog)
        layout.addWidget(self.about_button)
        central = QWidget()
        central.setLayout(layout)

        self.close_button = QPushButton("Avslutt")
        self.close_button.setStyleSheet(self.button_style)
        self.close_button.clicked.connect(self.close)

        self.race_button = QPushButton("Velg løp")
        self.race_button.setStyleSheet(self.button_style)
        self.race_button.setFixedWidth(150)
        self.race_button.setToolTip("Velg et annet løp.")
        self.race_button.clicked.connect(self.select_race)

        self.move_button = QPushButton("\u21D2        (F2)")
        self.move_button.setStyleSheet(self.button_style)
        font = QFont("Segoe UI Symbol")  # "Segoe UI Symbol" eller "Arial", "Consolas", "Fira Code"
        font.setPointSize(12)
        self.move_button.setFont(font)
        self.move_button.setFixedWidth(200)
        self.move_button.setToolTip("Flytt valgte klasser over til Trekkeplan, i den gruppen du har valgt (bås/ slep.")
        self.move_button.clicked.connect(self.move_class_to_plan)
        # F2 simulerer trykk på knappen.
        self.move_shortcut = QShortcut(QKeySequence("F2"), self)
        self.move_shortcut.setContext(Qt.WidgetShortcut)  # Kun aktiv når hovedvinduet har fokus
#        move_shortcut.activated.connect(parent.move_button.click)  # Simulerer knappetrykk
#        parent.move_shortcut.activated.connect(lambda: print("F2 trykket"))  # Simulerer knappetrykk

        self.remove_button = QPushButton("\u21D0        (F3)")
        self.remove_button.setStyleSheet(self.button_style)
        self.remove_button.setFont(font)
        self.remove_button.setFixedWidth(200)
        self.remove_button.setToolTip("Fjern valgt klasse fra Trekkeplan")
        self.remove_button.clicked.connect(self.delete_class_start_row)

        self.add_block_button = QPushButton("➕ Legg til")
        self.add_block_button.setStyleSheet(self.button_style)
        self.add_block_button.setFixedWidth(157)
        self.add_block_button.setToolTip("Legg til en ny bås/slep med vedier fra feltene over.\nHvis du har valgt ut en rad i tabellen under,\nvil bås feltet bli hentet herfra.")
        self.add_block_button.clicked.connect(self.add_block_lag)

        self.draw_start_times_button = QPushButton("Trekk starttider")
        self.draw_start_times_button.setStyleSheet(self.button_style)
        self.draw_start_times_button.setFixedWidth(150)
        self.draw_start_times_button.setToolTip("Trekk starttider for alle klasser i trekkeplanen.")
        self.draw_start_times_button.clicked.connect(self.draw_start_times)

        self.clear_start_times_button = QPushButton("Fjern starttider")
        self.clear_start_times_button.setStyleSheet(self.button_style)
        self.clear_start_times_button.setFixedWidth(150)
        self.clear_start_times_button.setToolTip("Fjern starttider for alle klasser i trekkeplanen.")
        self.clear_start_times_button.clicked.connect(self.clear_start_times)

        self.club_mates_button = QPushButton("Splitt klubbkamerater")
        self.club_mates_button.setStyleSheet(self.button_style)
        self.club_mates_button.setFixedWidth(150)
        self.club_mates_button.setToolTip("Løpere fra samme klubb som starter etter hverandre i samme klasse.")
        self.club_mates_button.clicked.connect(self.handle_club_mates)

        self.startListButton = QPushButton("Startliste")
        self.startListButton.setStyleSheet(self.button_style)
        self.startListButton.setFixedWidth(150)
        self.startListButton.setToolTip("Lag startliste pr. klasse.")
        self.startListButton.clicked.connect(self.make_startlist)

        self.starterListButton = QPushButton("Starter-liste")
        self.starterListButton.setStyleSheet(self.button_style)
        self.starterListButton.setFixedWidth(150)
        self.starterListButton.setToolTip("Lag startliste pr. starttid.")
        self.starterListButton.clicked.connect(self.make_starterlist)

        self.make_layout(title_block_lag, title_class_start, title_first_start, title_last_start, title_duration, title_utilization, title_non_planned)

        #        parent.load_button.clicked.connect(parent.load_data)
        #
        # Les fra MySQL initielt.
        #
        logging.debug("refresh 1: %s", self.race_id)
        self.refresh_race_times(self.race_id)

        if not self.race_name: self.setWindowTitle("Brikkesys/SvR Trekkeplan - ")
        else: self.setWindowTitle("Brikkesys/SvR Trekkeplan - " + self.race_name + "   " + self.race_date_db.isoformat() )
        table_font = self.table_not_planned.font()
        self.setFont(table_font)

        self.setWindowIcon(QIcon(self.icon_path))

        self.field_first_start.editingFinished.connect(self.first_start_edited)

        control.refresh_table(self, self.table_not_planned)
        self.after_plan_changed(None)

        self.table_not_planned.setColumnHidden(0, True)
        self.table_not_planned.sortItems(1, order=Qt.AscendingOrder)

        self.table_block_lag.setColumnHidden(0, True)
        self.table_block_lag.setColumnHidden(1, True)
        self.table_block_lag.sortItems(2, order=Qt.AscendingOrder)

        self.table_class_start.setColumnHidden(0, True)
        self.table_class_start.setColumnHidden(1, True)
        self.table_class_start.setColumnHidden(4, True) # Sortorder

        self.table_class_start.itemChanged.connect(self.class_start_item_changed)

#        parent.print_col_width(parent.table_not_planned)
#        parent.print_col_width(parent.table_block_lag)
#        parent.print_col_width(parent.table_class_start)

        # Behold samme farge når table ikke er i fokus.
        self.keep_selection_colour(self.table_not_planned)
        self.keep_selection_colour(self.table_block_lag)
        self.keep_selection_colour(self.table_class_start)

        # Kontekstmeny med funksjonstast.
        self.menu_non_planned = QMenu(self)
        self.action_moveto_plan = QAction("Flytt til planen.", self)
        self.action_nonplanned_hide = QAction("Skjul valgte klasser.", self)
        self.action_nonplanned_show = QAction("Vis skjulte klasser igjen.", self)
        self.menu_non_planned.addAction(self.action_moveto_plan)
        self.table_not_planned.addAction(self.action_moveto_plan)
        self.action_moveto_plan.setShortcut("F2")
        self.menu_non_planned.addAction(self.action_nonplanned_hide)
        self.menu_non_planned.addAction(self.action_nonplanned_show)

        self.menu_head = QMenu(self)
        self.menu_head.addAction(self.action_nonplanned_show)

        self.menu_blocklag = QMenu(self)
        self.action_delete_blocklag = QAction("Slett rad", self)
        self.menu_blocklag.addAction(self.action_delete_blocklag)

        self.menu_class_start = QMenu(self)
        self.action_move_up = QAction("Dytt klassen opp", self)
        self.action_move_down = QAction("Dytt klassen ned", self)
        self.action_rem_classstart = QAction("Fjern klassen fra planen", self)
        self.action_rem_bl_start = QAction("Fjern hele bås/slep seksjon", self)
        self.action_rem_all_start = QAction("Fjern alle fra planen", self)
        self.action_move_up.setShortcut("F5")
        self.action_move_down.setShortcut("F6")
        self.action_rem_classstart.setShortcut("F3")
        self.menu_class_start.addAction(self.action_move_up)
        self.menu_class_start.addAction(self.action_move_down)
        self.menu_class_start.addAction(self.action_rem_classstart)
        self.table_class_start.addAction(self.action_rem_classstart)
        self.table_class_start.addAction(self.action_move_up)
        self.table_class_start.addAction(self.action_move_down)

        self.menu_class_start.addAction(self.action_rem_bl_start)
        self.menu_class_start.addAction(self.action_rem_all_start)

        self.action_moveto_plan.triggered.connect(lambda: self.move_class_to_plan())
        self.action_nonplanned_hide.triggered.connect(lambda: self.hide_selected_rows())
        self.action_nonplanned_show.triggered.connect(lambda: self.show_hided_rows())
        self.action_delete_blocklag.triggered.connect(lambda: self.delete_blocklag_row())

        self.action_move_up.triggered.connect(lambda: self.class_start_up())
        self.action_move_down.triggered.connect(lambda: self.class_start_down())
        self.action_rem_classstart.triggered.connect(lambda: self.delete_class_start_row())
        self.action_rem_bl_start.triggered.connect(lambda: self.delete_class_start_block_lag())
        self.action_rem_all_start.triggered.connect(lambda: self.delete_class_start_all())

    def make_layout(self, title_block_lag: QLabel | QLabel, title_class_start: QLabel | QLabel,
                    title_first_start: QLabel | QLabel, title_last_start: QLabel | QLabel, title_duration: QLabel | QLabel, title_utilization: QLabel | QLabel, title_non_planned: QLabel | QLabel):
        #
        # Layout
        #
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        center_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.StyledPanel)
        center_frame.setFrameShadow(QFrame.Plain)
        center_frame.setLayout(center_layout)
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.StyledPanel)
        bottom_frame.setFrameShadow(QFrame.Plain)
        bottom_frame.setLayout(bottom_layout)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(center_frame)
        main_layout.addWidget(bottom_frame)

        top_layout.addWidget(self.race_button)
        top_layout.addWidget(self.help_button)
        top_layout.addWidget(self.about_button)
        top_layout.addWidget(title_first_start)
        top_layout.addWidget(self.field_first_start)
        top_layout.addWidget(title_last_start)
        top_layout.addWidget(self.field_last_start)
        top_layout.addWidget(title_duration)
        top_layout.addWidget(self.field_duration)
        top_layout.addWidget(title_utilization)
        top_layout.addWidget(self.field_utilization)
        top_layout.addStretch()

        column1_layout = QVBoxLayout()
#        column2_layout = QVBoxLayout()
        new_blocklag_layout = QHBoxLayout()
        column3_layout = QVBoxLayout()
        column4_layout = QVBoxLayout()
#        button_layout = QHBoxLayout()

        column1_layout.addWidget(title_non_planned)
        column1_layout.addWidget(self.table_not_planned)
        column1_layout.addStretch()

#        column2_layout.addWidget(title_first_start)
#        column2_layout.addWidget(parent.field_first_start)
#        column2_layout.addSpacing(200)
#        column2_layout.addWidget(parent.move_button)
#        column2_layout.addStretch()

        new_blocklag_layout.addWidget(self.field_block)
        new_blocklag_layout.addWidget(self.field_lag)
        new_blocklag_layout.addWidget(self.field_gap)
        new_blocklag_layout.addStretch()

        button_row1_layout = QHBoxLayout()
        button_row1_layout.addStretch()
        button_row1_layout.addWidget(self.move_button)
        button_row1_layout.addStretch()
        button_row2_layout = QHBoxLayout()
        button_row2_layout.addStretch()
        button_row2_layout.addWidget(self.remove_button)
        button_row2_layout.addStretch()


        column3_layout.addWidget(title_block_lag)
        column3_layout.addLayout(new_blocklag_layout)
        column3_layout.addWidget(self.add_block_button)
        column3_layout.addWidget(self.table_block_lag)
        column3_layout.addStretch()
        column3_layout.addLayout(button_row1_layout)
        column3_layout.addStretch()
        column3_layout.addLayout(button_row2_layout)
        column3_layout.addStretch()

#        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
#        column3_layout.addItem(spacer)

        bottom_layout.addWidget(self.startListButton)
        bottom_layout.addWidget(self.starterListButton)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.draw_start_times_button)
        bottom_layout.addWidget(self.club_mates_button)
        bottom_layout.addWidget(self.clear_start_times_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_button)

        header_class_start_layout = QHBoxLayout()
#        header_class_start_layout.addWidget(parent.move_button)
        header_class_start_layout.addWidget(title_class_start)

        column4_layout.addLayout(header_class_start_layout)
        column4_layout.addWidget(self.table_class_start)
        column4_layout.addStretch()

        center_layout.addLayout(column1_layout)
#        center_layout.addLayout(column2_layout)
        center_layout.addLayout(column3_layout)
        center_layout.addLayout(column4_layout)
        center_layout.addStretch()

        self.setLayout(main_layout)

    def refresh_race_times(self, raceid):
        logging.debug("refresh_race_times")
        rows0, columns0 = queries.read_race(self.conn_mgr, self.race_id)
        if not rows0: return
        race = rows0[0]
        self.race_name = race[1]
        self.race_date_db: datetime.date = race[2]
        self.race_first_start: datetime.datetime = race[3]
        self.drawplan_changed: datetime.datetime = race[4]
        self.draw_time: datetime.datetime = race[5]

        logging.debug("datetime type: %s", type(self.race_date_db))

        if self.race_first_start:
            q_time = QTime(self.race_first_start.hour, self.race_first_start.minute,
                                self.race_first_start.second)
        else: q_time = QTime(0,0)
        self.field_first_start.setTime(q_time)

    def populate_table(self, table, columns: list[any], rows):
        logging.debug("populate_table")
        self.table_class_start.blockSignals(True)
        table.clearContents()
        is_sorted = table.isSortingEnabled()
        if is_sorted: table.setSortingEnabled(False)
        table.setColumnCount(len(columns))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(columns)
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = None
                value_type = type(value)
                logging.debug("populate_table value_type: %s", value_type)

                item = DrawPlanTableItem.from_value(value)
                table.setItem(row_idx, col_idx, item)
        if is_sorted: table.setSortingEnabled(True)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.table_class_start.blockSignals(False)
        logging.info("populate_table end")

    def keep_selection_colour(self, table):
        logging.info("keep_selection_colour")
        palett = table.palette()
#        dark_blue = QColor(0, 120, 215)  # Windows 10 blå
#        dark_blue = QColor(173, 216, 230)  # Windows 10 blå
#        dark_blue = QColor(70, 130, 180)  # Windows 10 blå
        default_farge = QApplication.palette().color(QPalette.Highlight)
        palett.setColor(QPalette.Active, QPalette.Highlight, default_farge)
        palett.setColor(QPalette.Inactive, QPalette.Highlight, default_farge)

        white = QColor(Qt.white)
        palett.setColor(QPalette.Active, QPalette.HighlightedText, white)
        palett.setColor(QPalette.Inactive, QPalette.HighlightedText, white)
        table.setPalette(palett)

    def first_start_edited(self):
        logging.info("first_start_edited")
        # Update first start-time, then rebuild redundant in class_starts, and reread.

        new_first_datetime = datetime.datetime.combine(self.race_date_db, self.field_first_start.time().toPyTime())
        logging.debug("first_start_edited new_first_datetime: %s", new_first_datetime)

        # Ta vare på seletert rad, for reselekt.
        selected_row_id = None
        selected = self.table_block_lag.selectionModel().selectedRows()
        logging.debug("first_start_edited selected: %s", selected)
        blocklagid = None
        if selected:
            selected_row_id = selected[0].row()
            blocklagid = self.table_block_lag.item(selected_row_id, 0)

        logging.debug("first_start_edited selected_row_id: %s", selected_row_id)

        control.first_start_edited(self, self.race_id, new_first_datetime)
        control.refresh_table(self, self.table_class_start)

        self.after_plan_changed(blocklagid)


    def show_not_planned_menu(self, pos):
        logging.info("show_not_planned_menu")
        row_inx = self.table_not_planned.rowAt(pos.y())
        logging.debug("row_inx: %s", row_inx)
        if row_inx < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_non_planned.exec_(self.table_not_planned.viewport().mapToGlobal(pos))

    def show_not_planned_header_menu(self, pos):
        logging.info("show_not_planned_header_menu")
        # Høyreklikk på kolonneheader
        self.menu_head.exec_(self.table_not_planned.viewport().mapToGlobal(pos))

    def show_class_start_menu(self, pos):
        logging.info("show_class_start_menu")
        row_inx = self.table_class_start.rowAt(pos.y())
        if row_inx < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return

        self.menu_class_start.exec_(self.table_class_start.viewport().mapToGlobal(pos))


    def show_block_lag_menu(self, pos):
        logging.info("show_block_lag_menu")
        row_inx = self.table_block_lag.rowAt(pos.y())
        if row_inx < 0:
            logging.debug("Ingen rad under musepeker – meny avbrytes")
            return
        self.menu_blocklag.exec_(self.table_block_lag.viewport().mapToGlobal(pos))

    def delete_blocklag_row(self):
        logging.info("delete_blocklag_row")
        selected = self.table_block_lag.selectionModel().selectedRows()
        if not selected:
            return
        row_id = selected[0].row()

        blocklagid = self.table_block_lag.model().index(row_id, 0).data()
        blockid = self.table_block_lag.model().index(row_id, 1).data()
        block = self.table_block_lag.model().index(row_id, 2).data()
        lag = self.table_block_lag.model().index(row_id, 3).data()

        returned = control.delete_blocklag(self, self.race_id, blocklagid, blockid)
        if returned:
            self.show_message(returned)
        else:
            self.after_plan_changed(None)

    def show_message(self, tekst):
        logging.info("show_message")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Info")
        msg.setText(tekst)
        msg.exec_()

    def delete_class_start_row(self):
        logging.info("delete_class_start_row")
        selected = self.table_class_start.selectionModel().selectedRows()
        if not selected:
            self.show_message("Du må velge klassen som skal fjernes fra planen!")
            return
        row_id = selected[0].row()

        classstartid = self.table_class_start.model().index(row_id, 0).data()
        blocklagid = self.table_class_start.model().index(row_id, 1).data()
        klasse = self.table_class_start.model().index(row_id, 4).data()

        control.delete_class_start_row(self, self.race_id, classstartid)

        control.refresh_table(self, self.table_not_planned)

        self.after_plan_changed(blocklagid)

    def after_plan_changed(self, blocklagid):
        logging.info("after_plan_changed")
        max_next_datetime = control.refresh_table(self, self.table_block_lag)

        utilization = self.rebuild_blocklag_idle(self.table_block_lag, max_next_datetime)

        logging.debug("max_next_datetime: %s", max_next_datetime)
        self.set_last_start_time(max_next_datetime, utilization)
        control.refresh_table(self, self.table_class_start)

        # Re-selekt!
        self.select_by_id(self.table_block_lag, blocklagid)

        # Refarge valgbare
        self.table_class_start.update_filter()

    def rebuild_blocklag_idle(self, table, race_nexttime):
        logging.debug("rebuild_blocklag_idle: %s", race_nexttime)

        if race_nexttime is None or self.race_first_start is None:
            return
        duration = race_nexttime - self.race_first_start
        logging.debug("duration: %s", duration)

        sum_idletime = datetime.timedelta(0)
        count_idletime = 0
        for row_idx in range(table.rowCount()):
            item = table.item(row_idx, 5)
            if item is None:
                continue

            # Hent underliggende verdi (skal være datetime)
            blocklag_nexttime = item.data(Qt.UserRole)
            logging.debug("starttid_bås verdi: %s", blocklag_nexttime)
            logging.debug("starttid_bås type: %s", type(blocklag_nexttime))
            if not isinstance(blocklag_nexttime, datetime.datetime):
                continue

            # Beregn differanse
            idletime = race_nexttime - blocklag_nexttime  # timedelta
            idle_ratio = 1 if duration == datetime.timedelta(0) else idletime / duration
            sum_idletime = sum_idletime + idletime
            count_idletime = count_idletime + 1

            # Lag nytt item med differansen
            idle_item = DrawPlanTableItem.from_value(idletime)
            idle_item.setBackground(self.color_idle_time(idle_ratio))
            table.setItem(row_idx, 6, idle_item)

        if duration * count_idletime > datetime.timedelta(0):
            sum_idle_ratio = sum_idletime / (duration * count_idletime)
        else:
            sum_idle_ratio = 1
        utilization = 1 - sum_idle_ratio

        sum_color = self.color_idle_time(sum_idle_ratio)
        hex_color = sum_color.name()
        existing_style = self.field_utilization.styleSheet()
        self.field_utilization.setStyleSheet(existing_style + f"background-color: {hex_color};")

        return utilization

    def color_idle_time(self, idle_ratsio):
        # Juster intensitet (lav = lys rosa, høy = mørk rød)
        r = int(255)
        g = int(200 * (1 - idle_ratsio))  # fra 200 ned mot 0
        b = int(200 * (1 - idle_ratsio))  # fra 200 ned mot 0

        return QColor(r, g, b)

    #
    # Slett classStart rader som tilhører valgt bås/slep
    #
    def delete_class_start_block_lag(self):
        logging.info("delete_class_start_block_lag")
        selected = self.table_class_start.selectionModel().selectedRows()
        if not selected:
            return
        row_id = selected[0].row()

        classstartid = self.table_class_start.model().index(row_id, 0).data()
        blocklagid = self.table_class_start.model().index(row_id, 1).data()
        klasse = self.table_class_start.model().index(row_id, 4).data()

        control.delete_class_start_rows(self, self.race_id, blocklagid)

        control.refresh_table(self, self.table_not_planned)
#        control.refresh_table(parent, parent.table_class_start)
        self.after_plan_changed(blocklagid)

    #
    # Slett alle classStart rader for dette løpet.
    #
    def delete_class_start_all(self):
        logging.info("delete_class_start_all")
        control.delete_class_start_all(self, self.race_id)

        control.refresh_table(self, self.table_not_planned)
        control.refresh_table(self, self.table_class_start)

        self.after_plan_changed(None)

    def hide_selected_rows(self):
        logging.info("hide_selected_rows")
        model_indexes = self.table_not_planned.selectionModel().selectedRows()

        classids = set()
        for indeks in model_indexes:
            rad = indeks.row()
            classid = self.table_not_planned.item(rad, 0)
            classids.add(classid.text())
        control.insert_class_start_nots(self, self.race_id, classids)
        # Refresh
        control.refresh_table(self, self.table_not_planned)

    def show_hided_rows(self):
        logging.info("show_hided_rows")
        control.delete_class_start_not(self, self.race_id)
        # Refresh
        control.refresh_table(self, self.table_not_planned)

    def class_start_down_up(self, step):
        logging.info("class_start_down_up")
        selected = self.table_class_start.selectionModel().selectedRows()
        if not selected:
            self.show_message("Du må velge klassen som skal flyttes et hakk!")
            return
        row_id = selected[0].row()

        clas_start_id = self.table_class_start.model().index(row_id, 0).data()
        blocklag_id = self.table_class_start.model().index(row_id, 1).data()

        control.class_start_down_up(self, clas_start_id, step)
        control.refresh_table(self, self.table_class_start)
#        parent.select_by_id(parent.table_block_lag, blocklag_id) # Er allerede selektert.
        self.table_class_start.update_filter()
        self.select_by_id(self.table_class_start, clas_start_id)

    def class_start_down(self):
        logging.info("class_start_down")
        self.class_start_down_up(11) # Avstand 10 mellom hver.

    def class_start_up(self):
        logging.info("class_start_up")
        self.class_start_down_up(-11) # Avstand 10 mellom hver.

    def add_block_lag(self):
        logging.info("add_block_lag")
        if self.race_id == 0:
            self.show_message("Må velge et løp først!")
            return
        model_indexes = self.table_block_lag.selectionModel().selectedRows()
        if model_indexes:
            rad = model_indexes[0].row()
            blockid = self.table_block_lag.item(rad, 1).text()
            lag = self.field_lag.text()
            gap = self.field_gap.text()
            try:
                control.add_lag(self, blockid, lag, gap)
            except MyCustomError as e:
                self.show_message(e.message)
        else:
            block = self.field_block.text()
            if not block:
                self.show_message("Du må fylle inn navnet på båsen, \neller velge en rad fra tabellen under!")
                return
            lag = self.field_lag.text()
            if not lag: lag = 0
            gap = self.field_gap.text()
            if not gap: gap = 0
            try:
                control.add_block_lag(self, self.race_id, block, lag, gap)
            except MyCustomError as e:
                self.show_message(e.message)

        self.after_plan_changed(None)


    def move_class_to_plan(self):
        logging.info("move_class_to_plan")
        selected_model_rows = self.table_not_planned.selectionModel().selectedRows()
        if not selected_model_rows:
            self.show_message("Du må velge ei klasse å flytte til Trekkeplanen!")
            return
        elif (selected_model_rows.__len__() > 9):
            self.show_message("Du kan ikke flytte flere enn 9 klasser til Trekkeplanen i en runde!")
            return

        # Bås/slep
        block_lag_rows = self.table_block_lag.selectionModel().selectedRows()
        if not block_lag_rows:
            self.show_message("Du må velge et bås/tidsslep å flytte til!")
            return

        # Hvilken bås/slep skal klassen inn i?
        row_id = block_lag_rows[0].row()
        blocklag_id = int(self.table_block_lag.item(row_id, 0).text())
        gap = int(self.table_block_lag.item(row_id, 4).text())

        # Valgt rad styrer hvor i bås/slep-seksjonen den skal inn.
        class_start_rows = self.table_class_start.selectionModel().selectedRows()
        sort_value = 1000 # Hvis ingen rad er valgt, legges den til sist i gruppen.
        if class_start_rows:
            # En rad valgt. Ta plassen til denne, og skyv de andre lenger ned.
            row_id = class_start_rows[0].row()
            sort_value = int(self.table_class_start.item(row_id, 4).text())
            sort_value = sort_value-10 # Plass til 9 før denne.
        # Radene er sortert i den rekkefølgen de ble selektert.
        # Men vi ønsker de sortert som den visuelle sorteringen i bildet.
        sorted_selected = sorted(selected_model_rows, key=lambda index: index.row())
        for view_index in sorted_selected:
            model_index = self.table_not_planned.model().index(view_index.row(), 0)
            classid = self.table_not_planned.model().data(model_index)
            sort_value = sort_value+1
            control.insert_class_start(self, self.race_id, blocklag_id, classid, gap, sort_value)

        # Oppdater redundante kolonner og oppfrisk tabellene.
        control.rebuild_class_starts(self, self.race_id)
        control.refresh_table(self, self.table_not_planned)

        self.after_plan_changed(str(blocklag_id))

    def get_row_idx(self, table: QTableWidget, col_idx: int, col_value):
        logging.info("get_row_idx")
        logging.debug("get_row_idx: %s: %s", col_idx, col_value)
        for row_idx in range(table.rowCount()):
            item = table.item(row_idx, col_idx).text()
            if item == str(col_value):
                return row_idx
        logging.error("System error: return row_idx=None")
        return None

    def show_about_dialog(self):
        dialog = AboutDialog()
        dialog.setWindowIcon(QIcon(self.icon_path))
        dialog.exec_()


    def select_race(self: QWidget):
        logging.info("select_race")
        dialog = SelectRaceDialog(self)
        dialog.setWindowIcon(QIcon(self.icon_path))

        logging.info("select_race 2")

        if dialog.exec_() == QDialog.Accepted:
            valgt_id = dialog.selected_race_id

            self.race_id = valgt_id
            control.refresh_table(self, self.table_not_planned)
            self.refresh_race_times(self.race_id)
            self.setWindowTitle("Brikkesys/SvR Trekkeplan - " + self.race_name + "   " + self.race_date_db.isoformat())
            self.put_raceid_in_registry(self.race_id) # I registry
            self.after_plan_changed(None)
        else:
            logging.debug("Brukeren avbrøt")

    def handle_club_mates(self):
        logging.info("handle_club_mates")
        dialog = SplitClubMates(self)
        dialog.setWindowIcon(QIcon(self.icon_path))
        dialog.exec_() # modal visning.

    def print_col_width(self, table):
        for kol in range(table.columnCount()):
            bredde = table.columnWidth(kol)
            logging.debug(f"Kolonne {kol}: {bredde}px")

    def set_fixed_widths(self, table, widths):
        for col_inx, width in enumerate(widths):
            table.setColumnWidth(col_inx, width)

    def class_start_item_changed(self, item):
        logging.info("class_start_item_changed")
        self.table_class_start.blockSignals(True)
        idx_col = item.column()
        idx_row = item.row()
#        if parent.table_class_start.hasFocus():
        if idx_col in [10,11]: # Antall ledige før og etter.
            new_value = item.text().strip()
            if new_value == "": new_value = None
            item.setText(new_value)
            classstartid = self.table_class_start.item(idx_row, 0).text()
            blocklagid = self.table_class_start.item(idx_row, 1).text()
            if idx_col==10:
                control.class_start_free_updated(self, self.race_id, classstartid, blocklagid, new_value, 1)
            if idx_col==11:
                control.class_start_free_updated(self, self.race_id, classstartid, blocklagid, new_value, 2)

        self.table_class_start.blockSignals(False)

    def put_raceid_in_registry(self, raceid: int):
        settings = QSettings("Brikkesys_svr", "Trekkeplan")
        settings.setValue("Race_id", raceid)

    def get_raceid_from_registry(self) -> int | None:
        settings = QSettings("Brikkesys_svr", "Trekkeplan")
        verdi = settings.value("Race_id", None)
        return int(verdi) if verdi is not None else 0

    def adjust_table_hight(self, table, max_height = 600):
        logging.info("adjust_table_hight")
        header_h = table.horizontalHeader().height()
        row_height = header_h
        scrollbar_h = table.horizontalScrollBar().height() if table.horizontalScrollBar().isVisible() else 0
        total_height = header_h + (row_height * table.rowCount()) + scrollbar_h + 2  # +2 for ramme
        limited_height = min(total_height, max_height)
        table.setFixedHeight(limited_height)

    def adjust_table_width(self, table, extra_margin=2):
        logging.info("adjust_table_width")
        total_width = sum(table.columnWidth(kol) for kol in range(table.columnCount()))
        vertical_scroll = table.verticalScrollBar().sizeHint().width() # if table.verticalScrollBar().isVisible() else 0
        frame = table.frameWidth() * 2
        table.setFixedWidth(total_width + vertical_scroll + frame + extra_margin)
        logging.debug("vertical_scroll: %s", vertical_scroll)

    def draw_start_times(self):
        logging.info("draw_start_times")
        if self.ask_confirmation("Trekk starttider for klassene i planen?"):
            control.draw_start_times(self, self.race_id)
        else:
            logging.debug("Brukeren avbrøt")


    def clear_start_times(self):
        logging.info("clear_start_times")

        if self.ask_confirmation("Slette alle starttider?"):
            control.clear_start_times(self, self.race_id)
        else:
            logging.debug("Brukeren avbrøt")


    def make_startlist(self):
        logging.info("make_startlist")
        control.make_startlist(self, self.race_id)

    def make_starterlist(self):
        logging.info("make_starterlist")
        control.make_starterlist(self, self.race_id)

    def open_help(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.pdf_path))

    # Override closeEvent.
    def closeEvent(self, event):
        size = self.size()
        logging.debug(f"Vinduet avsluttes med størrelse: {size.width()} x {size.height()}")
        super().closeEvent(event)

    def set_table_sizes(self, table, col_sizes):
        self.set_fixed_widths(table, col_sizes)
        table.resizeRowsToContents()
        self.adjust_table_hight(table)
        self.adjust_table_width(table)

    def select_by_id(self, table, id, col=0):
        logging.info("select_by_id id: %s", id)
        logging.debug("select_by_id id type: %s", type(id))
        for row_idx in range(table.rowCount()):
            item = table.item(row_idx, col).text()
            logging.debug("select_by_id item type, value: %s, %s", type(item), item)
            if item == id:
                logging.info("select_by_id: item found %s", item)
                table.selectRow(row_idx)
                return
        logging.error("Table row not found, id=%s", id)

    def set_last_start_time(self, max_next_datetime: datetime.datetime | None, utilization: float):
        logging.info("set_last_start_time: %s", max_next_datetime)
        q_time_duration = None
        if max_next_datetime is not None and self.race_first_start is not None:
            q_time_last = QTime(max_next_datetime.hour, max_next_datetime.minute,
                                max_next_datetime.second)
            q_time_duration = max_next_datetime - self.race_first_start
            logging.debug("q_time_duration: %s", q_time_duration)
        else: q_time_last = QTime(0, 0)

        utilization_percent: int = round(utilization * 100)

        self.field_last_start.setTime(q_time_last)
        self.field_duration.setText(self.format_duration(q_time_duration))
        self.field_utilization.setText(str(utilization_percent))

    def format_duration(self, td: datetime.timedelta) -> str:
        if td is None: return "      "
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02}:{seconds:02}"

    def max_value(self, rows, col):
        logging.info("max_value")
        max = None
        for row in rows:
            if max is None:
                max = row[col]
            elif row[col] > max:
                max = row[col]
        logging.debug("max_value, type: %s", type(max))
        logging.debug("max_value, max: %s", max)
        return max

    # Called from BlockLineEdit
    def block_focus_action(self):
        logging.info("block_focus_action")
        # Når bruker entrer Bås-feltet, så deselekterer vi valgt rad.
        # Hvis ikke så er det båsen i valgt rad som gjelder når man trykker +.
        self.table_block_lag.clearSelection()

    def ask_confirmation(parent, message: str) -> bool:
        reply = QMessageBox.question(
            parent,
            "Bekreft handling",
            message,
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        return reply == QMessageBox.Ok

