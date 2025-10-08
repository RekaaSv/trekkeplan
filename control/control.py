from db import queries


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
