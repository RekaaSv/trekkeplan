from db import queries
from gui.velg_løp_dialog import SelectRaceDialog


def first_start_edited(raceId, str_new_first_start):
    # Update first start-time, then rebuild redundant columns in class_starts.
    queries.upd_first_start(raceId, str_new_first_start)
    queries.rebuild_class_starts(raceId)

def delete_class_start_row(raceId, classstartId):
    queries.delete_class_start_row(raceId, classstartId)

def delete_class_start_rows(raceId, blocklagId):
    queries.delete_class_start_rows(raceId, blocklagId)

def delete_blocklag(raceId, blocklagId, blockId):
    returned = queries.delete_blocklag(raceId, blocklagId)
    if returned:
        print("delete_blocklag slettet OK")
        # Prøv å slett bås også.
        returned2 = queries.delete_block(raceId, blockId)
        if returned2: print("delete_block slettet OK")
        return None
    else:
        return "Fjern tilhørende klasser fra planen, og prøv igjen!"

def insert_class_start_nots(raceId, classsIds):
#    print("Control. insert_class_start_nots start")
    for classid in classsIds:
#       print("Control. Inserting class start not=" + classid)
        queries.insert_class_start_not(raceId, classid)

def delete_class_start_not(raceId):
    queries.delete_class_start_not(raceId)


def add_block_lag(raceId, block, lag, gap):
    blockid = queries.add_block(raceId, block)
    blocklagid = queries.add_blocklag(blockid, lag, gap)


def add_lag(blockid, lag, gap):
    blocklagid = queries.add_blocklag(blockid, lag, gap)

def insert_class_start(raceId, blocklagId, classId, timegap, sortorder):
    print("control.insert_class_start")
    queries.insert_class_start(raceId, blocklagId, classId, timegap, sortorder)


def refresh_table(self, table):
    print("control.refresh_table")
    print("tabell:",table )
    print("tabell:",table )
    rows, columns = None, None
    if table == self.tableNotPlanned:
        rows, columns = queries.read_not_planned(self.raceId)
    elif table == self.tableBlockLag:
        rows, columns = queries.read_block_lags(self.raceId)
    elif table == self.tableClassStart:
        rows, columns = queries.read_class_starts(self.raceId)
#    elif table == SelectRaceDialog.table_race:
    elif table == self.table_race:
        print("SelectRaceDialog.table_race")
        rows, columns = queries.read_race_list()
        print(columns)
    else:
        raise Exception("Systemfeil!")

    self.populate_table(table, columns, rows)

def refresh_raise_list(self, dialog):
    print("control.refresh_table")
    rows, columns = None, None
    print("SelectRaceDialog.table_race")
    rows, columns = queries.read_race_list()
    print(columns)

    self.populate_table(dialog.table_race, columns, rows)

    dialog.table_race.setColumnHidden(3, True)

"""
    Leser høyeste Neste (neste starttid) for bås/slep blocklagid
"""
def read_blocklag_neste(self, blocklagid ):
    print("control.read_blocklag_neste")
    rows, columns = queries.read_block_lag(blocklagid)
    print("control.read_blocklag_neste", rows, columns)
    return rows[0][5]
    # return rows

