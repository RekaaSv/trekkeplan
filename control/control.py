from db import queries


def first_start_edited(self, raceId, str_new_first_start):
    if self.log: print("control.first_start_edited")
    # Update first start-time, then rebuild redundant columns in class_starts.
    queries.upd_first_start(raceId, str_new_first_start)
    queries.rebuild_class_starts(raceId)

def delete_class_start_row(self, raceId, classstartId):
    if self.log: print("control.delete_class_start_row")
    queries.delete_class_start_row(raceId, classstartId)

def delete_class_start_rows(self, raceId, blocklagId):
    if self.log: print("control.delete_class_start_rows")
    queries.delete_class_start_rows(raceId, blocklagId)

def delete_blocklag(self, raceId, blocklagId, blockId):
    if self.log: print("control.delete_blocklag")
    returned = queries.delete_blocklag(raceId, blocklagId)
    if returned:
#        print("delete_blocklag slettet OK")
        # Prøv å slett bås også.
        returned2 = queries.delete_block(raceId, blockId)
        if returned2: print("delete_block slettet OK")
        return None
    else:
        return "Fjern tilhørende klasser fra planen, og prøv igjen!"

def insert_class_start_nots(self, raceId, classsIds):
    if self.log: print("control.insert_class_start_nots")
    #    print("Control. insert_class_start_nots start")
    for classid in classsIds:
#       print("Control. Inserting class start not=" + classid)
        queries.insert_class_start_not(raceId, classid)

def delete_class_start_not(self, raceId):
    if self.log: print("control.delete_class_start_not")
    queries.delete_class_start_not(raceId)


def add_block_lag(self, raceId, block, lag, gap):
    if self.log: print("control.add_block_lag")
    blockid = queries.add_block(raceId, block)
    blocklagid = queries.add_blocklag(blockid, lag, gap)


def add_lag(self, blockid, lag, gap):
    if self.log: print("control.add_lag")
    blocklagid = queries.add_blocklag(blockid, lag, gap)

def insert_class_start(self, raceId, blocklagId, classId, timegap, sortorder):
    if self.log: print("control.insert_class_start")
    queries.insert_class_start(raceId, blocklagId, classId, timegap, sortorder)


def refresh_table(self, table):
    if self.log: print("control.refresh_table")
    print("table:",table )
    rows, columns = None, None
    if table == self.tableNotPlanned:
        rows, columns = queries.read_not_planned(self.raceId)
    elif table == self.tableBlockLag:
        rows, columns = queries.read_block_lags(self.raceId)
    elif table == self.tableClassStart:
        rows, columns = queries.read_class_starts(self.raceId)
    elif table == self.table_race:
        rows, columns = queries.read_race_list()
    else:
        raise Exception("Systemfeil!")

    self.populate_table(table, columns, rows)
    if table == self.tableClassStart:
        self.sett_redigerbare_kolonner(self.tableClassStart, [10, 11])

def refresh_race_list(self, dialog):
    if self.log: print("control.refresh_race_list")
    rows, columns = None, None
    rows, columns = queries.read_race_list()
#    print(columns)

    self.populate_table(dialog.table_race, columns, rows)

    dialog.table_race.setColumnHidden(3, True)

"""
    Leser høyeste Neste (neste starttid) for bås/slep blocklagid
"""
def read_blocklag_neste(self, blocklagid ):
    if self.log: print("control.read_blocklag_neste")
    rows, columns = queries.read_block_lag(blocklagid)
    print("control.read_blocklag_neste", rows, columns)
    return rows[0][5]
    # return rows


def class_start_free_updated(self, raceId, classstartid, blocklagid, new_value, cellno):
    if self.log: print("control.class_start_free_updated")
    print("Signal av")
    self.tableClassStart.blockSignals(True)
    if cellno==1:
        queries.upd_class_start_free_before(raceId, classstartid, new_value)
    elif cellno==2:
        queries.upd_class_start_free_after(raceId, classstartid, new_value)
    # Rebuild
    queries.rebuild_class_starts(raceId)
    refresh_table(self, self.tableClassStart)
    self.tableClassStart.oppdater_filter()

    # Hent verdi fra DB.
    neste = read_blocklag_neste(self, blocklagid)
    print("neste", neste)
    # Finn item og oppdater det med verdien fra basen.
    self.set_nexttime_on_blocklag(blocklagid, neste)
    print("Signal på")
    self.tableClassStart.blockSignals(False)
    print("control.class_start_free_updated end")
