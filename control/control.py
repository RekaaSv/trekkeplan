import datetime
import logging

from db import queries
from html.html_builder import HtmlBuilder


def first_start_edited(parent, race_id, new_first_start_datetime):
    logging.info("control.first_start_edited")
    # Update first start-time, then rebuild redundant columns in class_starts.
    queries.upd_first_start(parent.conn_mgr, race_id, new_first_start_datetime)
    logging.debug("control.first_start_edited new_first_start_datetime: %s", new_first_start_datetime)
    parent.race_first_start = new_first_start_datetime

    rebuild_class_starts(parent, race_id)

def delete_class_start_row(parent, race_id, classstart_id):
    logging.info("control.delete_class_start_row")
    queries.delete_class_start_row(parent.conn_mgr, race_id, classstart_id)
    rebuild_class_starts(parent, race_id)

def class_start_down_up(parent, id, step):
    logging.info("control.class_start_down_up")
    queries.class_start_down_up(parent.conn_mgr, id, step)
    rebuild_class_starts(parent, parent.race_id)

def delete_class_start_rows(parent, race_id, blocklag_id):
    logging.info("control.delete_class_start_rows")
    queries.delete_class_start_rows(parent.conn_mgr, race_id, blocklag_id)
    rebuild_class_starts(parent, race_id)

def delete_class_start_all(parent, race_id):
    logging.info("control.delete_class_start_all")
    queries.delete_class_start_all(parent.conn_mgr, race_id)
    rebuild_class_starts(parent, race_id)

def delete_blocklag(parent, race_id, blocklag_id, blockId):
    logging.info("control.delete_blocklag")
    returned = queries.delete_blocklag(parent.conn_mgr, race_id, blocklag_id)
    if returned:
        # Prøv å slett bås også.
        returned2 = queries.delete_block(parent.conn_mgr, race_id, blockId)
        if returned2: logging.info("delete_block slettet OK")
        return None
    else:
        return "Fjern tilhørende klasser fra planen, og prøv igjen!"

def insert_class_start_nots(parent, race_id, classsIds):
    logging.info("control.insert_class_start_nots")
    for classid in classsIds:
        queries.insert_class_start_not(parent.conn_mgr, race_id, classid)

def delete_class_start_not(parent, race_id):
    logging.info("control.delete_class_start_not")
    queries.delete_class_start_not(parent.conn_mgr, race_id)


def add_block_lag(parent, race_id, block, lag, gap):
    logging.info("control.add_block_lag")
    blockid = queries.add_block(parent.conn_mgr, race_id, block)
    queries.add_blocklag(parent.conn_mgr, blockid, lag, gap)


def add_lag(parent, blockid, lag, gap):
    logging.info("control.add_lag")
    queries.add_blocklag(parent.conn_mgr, blockid, lag, gap)

def insert_class_start(parent, race_id, blocklag_id, class_id, timegap, sortorder):
    logging.info("control.insert_class_start")
    queries.insert_class_start(parent.conn_mgr, race_id, blocklag_id, class_id, timegap, sortorder)


def refresh_table(parent, table):
    logging.info("control.refresh_table")
    max_next_time = None # For table_block_lag returneres max_next_time
    if table == parent.table_not_planned:
        logging.info("control.refresh_table table_not_planned")
        rows, columns = queries.read_not_planned(parent.conn_mgr, parent.race_id)
        col_widths = parent.col_widths_not_planned
    elif table == parent.table_block_lag:
        logging.info("control.refresh_table table_block_lag")
        rows, columns = queries.read_block_lags(parent.conn_mgr, parent.race_id)
        max_next_time = parent.max_value(rows, 5)
        logging.debug("control.refresh_table max_next_time: %s", max_next_time)
        col_widths = parent.col_widths_block_lag
    elif table == parent.table_class_start:
        logging.info("control.refresh_table table_class_start")
        rows, columns = queries.read_class_starts(parent.conn_mgr, parent.race_id)
        col_widths = parent.col_widths_class_start
    else:
        logging.error("Systemfeil!", exc_info=True)
        raise Exception("Systemfeil!")

    parent.populate_table(table, columns, rows)
    parent.set_table_sizes(table, col_widths)
    return max_next_time

def class_start_free_updated(parent, race_id, classstartid, blocklagid, new_value, cellno):
    logging.info("control.class_start_free_updated")
    logging.info("Signal av")
    parent.table_class_start.blockSignals(True)
    if cellno==1:
        queries.upd_class_start_free_before(parent.conn_mgr, race_id, classstartid, new_value)
    elif cellno==2:
        queries.upd_class_start_free_after(parent.conn_mgr, race_id, classstartid, new_value)
    # Rebuild
    rebuild_class_starts(parent, race_id)
    refresh_table(parent, parent.table_class_start)

    parent.after_plan_changed(blocklagid)

    parent.table_class_start.blockSignals(False)
    logging.debug("control.class_start_free_updated end")

def make_startlist(parent, race_id):
    logging.info("control.make_startlist")
    rows, columns = queries.sql_start_list(parent.conn_mgr, race_id)
    html = HtmlBuilder.grouped_rows_in_single_table(rows, columns, 0, "strong", 0)

    HtmlBuilder.download(html, "Startlist.html")

def make_starterlist(parent, race_id):
    logging.info("control.make_starterlist")
    rows, columns = queries.sql_starter_list(parent.conn_mgr, race_id)
    html = HtmlBuilder.grouped_rows_in_single_table(rows, columns, 5, "strong", 0)

    HtmlBuilder.download(html, "Starterlist.html")

def draw_start_times(parent, race_id):
    queries.draw_start_times(parent.conn_mgr, race_id)
    now = datetime.datetime.now()
    # Sett tidsstempel på at det er trukket, både i basen og global variabel.
    queries.upd_draw_time(parent.conn_mgr, race_id, now)
    parent.draw_time = now

    parent.show_message("Trekking foretatt, se Startliste!")

def clear_start_times(parent, race_id):
    queries.clear_start_times(parent.conn_mgr, race_id)
    parent.show_message("Starttider fjernet, se Startliste!")

def rebuild_class_starts(parent, race_id):
    queries.rebuild_class_starts(parent.conn_mgr, race_id)

    # Sett tidsstempel på at planen er endret, både i basen og global variabel.
    now = datetime.datetime.now()
    queries.upd_drawplan_changed(parent.conn_mgr, race_id, now)
    parent.drawplan_changed = now
