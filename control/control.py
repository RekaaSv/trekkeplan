import datetime
import logging

from db import queries
from html.html_builder import HtmlBuilder


def first_start_edited(self, raceId, str_new_first_start):
    logging.info("control.first_start_edited")
    # Update first start-time, then rebuild redundant columns in class_starts.
    queries.upd_first_start(self.conn_mgr, raceId, str_new_first_start)
    rebuild_class_starts(self, raceId)

def delete_class_start_row(self, raceId, classstartId):
    logging.info("control.delete_class_start_row")
    queries.delete_class_start_row(self.conn_mgr, raceId, classstartId)
    rebuild_class_starts(self, raceId)

def class_start_down_up(self, id, step):
    logging.info("control.class_start_down_up")
    queries.class_start_down_up(self.conn_mgr, id, step)
    rebuild_class_starts(self, self.raceId)

def delete_class_start_rows(self, raceId, blocklagId):
    logging.info("control.delete_class_start_rows")
    queries.delete_class_start_rows(self.conn_mgr, raceId, blocklagId)
    rebuild_class_starts(self, raceId)

def delete_class_start_all(self, raceId):
    logging.info("control.delete_class_start_all")
    queries.delete_class_start_all(self.conn_mgr, raceId)
    rebuild_class_starts(self, raceId)

def delete_blocklag(self, raceId, blocklagId, blockId):
    logging.info("control.delete_blocklag")
    returned = queries.delete_blocklag(self.conn_mgr, raceId, blocklagId)
    if returned:
        # Prøv å slett bås også.
        returned2 = queries.delete_block(self.conn_mgr, raceId, blockId)
        if returned2: logging.info("delete_block slettet OK")
        return None
    else:
        return "Fjern tilhørende klasser fra planen, og prøv igjen!"

def insert_class_start_nots(self, raceId, classsIds):
    logging.info("control.insert_class_start_nots")
    for classid in classsIds:
        queries.insert_class_start_not(self.conn_mgr, raceId, classid)

def delete_class_start_not(self, raceId):
    logging.info("control.delete_class_start_not")
    queries.delete_class_start_not(self.conn_mgr, raceId)


def add_block_lag(self, raceId, block, lag, gap):
    logging.info("control.add_block_lag")
    blockid = queries.add_block(self.conn_mgr, raceId, block)
    blocklagid = queries.add_blocklag(self.conn_mgr, blockid, lag, gap)


def add_lag(self, blockid, lag, gap):
    logging.info("control.add_lag")
    blocklagid = queries.add_blocklag(self.conn_mgr, blockid, lag, gap)

def insert_class_start(self, raceId, blocklagId, classId, timegap, sortorder):
    logging.info("control.insert_class_start")
    queries.insert_class_start(self.conn_mgr, raceId, blocklagId, classId, timegap, sortorder)


def refresh_table(self, table):
    logging.info("control.refresh_table")
    rows, columns = None, None
    col_widths = None
    max_next_time = None # For tableBlockLag returneres max_next_time
    if table == self.tableNotPlanned:
        logging.info("control.refresh_table tableNotPlanned")
        rows, columns = queries.read_not_planned(self.conn_mgr, self.raceId)
        col_widths = self.col_widths_not_planned
    elif table == self.tableBlockLag:
        logging.info("control.refresh_table tableBlockLag")
        rows, columns = queries.read_block_lags(self.conn_mgr, self.raceId)
        max_next_time = self.max_value(rows, 5)
        logging.debug("control.refresh_table max_next_time: %s", max_next_time)
        col_widths = self.col_widths_block_lag
    elif table == self.tableClassStart:
        logging.info("control.refresh_table tableClassStart")
        rows, columns = queries.read_class_starts(self.conn_mgr, self.raceId)
        col_widths = self.col_widths_class_start
    else:
        logging.error("Systemfeil!", exc_info=True)
        raise Exception("Systemfeil!")

    self.populate_table(table, columns, rows)
    self.set_table_sizes(table, col_widths)
    return max_next_time

def class_start_free_updated(self, raceId, classstartid, blocklagid, new_value, cellno):
    logging.info("control.class_start_free_updated")
    logging.info("Signal av")
    self.tableClassStart.blockSignals(True)
    if cellno==1:
        queries.upd_class_start_free_before(self.conn_mgr, raceId, classstartid, new_value)
    elif cellno==2:
        queries.upd_class_start_free_after(self.conn_mgr, raceId, classstartid, new_value)
    # Rebuild
    rebuild_class_starts(self, raceId)
    refresh_table(self, self.tableClassStart)

    self.after_plan_changed(blocklagid)

    self.tableClassStart.blockSignals(False)
    logging.debug("control.class_start_free_updated end")

def make_startlist(self, raceId):
    logging.info("control.make_startlist")
    rows, columns = queries.sql_start_list(self.conn_mgr, raceId)
    html = HtmlBuilder.grouped_rows_in_single_table(rows, columns, 0, "strong", 0)

    HtmlBuilder.download(html, "Startlist.html")

def make_starterlist(self, raceId):
    logging.info("control.make_starterlist")
    rows, columns = queries.sql_starter_list(self.conn_mgr, raceId)
    html = HtmlBuilder.grouped_rows_in_single_table(rows, columns, 5, "strong", 0)

    HtmlBuilder.download(html, "Starterlist.html")

def draw_start_times(self, raceId):
    queries.draw_start_times(self.conn_mgr, raceId)
    queries.upd_draw_time(self.conn_mgr, raceId, datetime.datetime.now())
    self.vis_brukermelding("Trekking foretatt, se Startliste!")

def clear_start_times(self, raceId):
    queries.clear_start_times(self.conn_mgr, raceId)
    self.vis_brukermelding("Starttider fjernet, se Startliste!")

def rebuild_class_starts(self, raceId):
    queries.rebuild_class_starts(self.conn_mgr, raceId)
    queries.upd_drawplan_changed(self.conn_mgr, raceId, datetime.datetime.now())
