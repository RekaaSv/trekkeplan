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
        return None
    else:
        return "Fjern tilhørende klasser fra planen, og prøv igjen!"