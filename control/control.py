from db import queries


def first_start_edited(raceId, str_new_first_start):
    # Update first start-time, then rebuild redundant columns in class_starts.
    queries.upd_first_start(raceId, str_new_first_start)
    queries.rebuild_class_starts(raceId)
