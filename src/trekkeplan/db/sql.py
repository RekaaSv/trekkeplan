import logging

import pymysql
from trekkeplan.control.errors import MyCustomError

def read_race_list(conn_mgr):
    logging.info("sql.read_race_list")
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT r.racedate Dag, r.name Løp, r.svr_first_start Starttid, r.id
FROM races r
ORDER BY r.racedate DESC, r.created DESC
"""
    cursor.execute(sql)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

"""
Løpere som har klubbkamerat i samme klasse rett før.
"""
def read_club_mates(conn_mgr, raceid):
    logging.info("sql.read_club_mates")
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT a.id, a.previd, a.classid
     , a.classname Klasse, a.name Løper, a.club Klubb, a.starttime Starttid FROM
(SELECT n.id, n.starttime
     , n.`name`
     , n.club
     , cl.id classid
     , cl.`name` classname
-- Bytte starttid nedover.
     , LAG(n.id) OVER (PARTITION BY cl.`name` ORDER BY n.starttime ASC) previd
     , LAG(n.club) OVER (PARTITION BY cl.`name` ORDER BY n.starttime ASC) prevclub
     , LEAD(n.id) OVER (PARTITION BY cl.`name` ORDER BY n.starttime ASC) nextid
     , LEAD(n.club) OVER (PARTITION BY cl.`name` ORDER BY n.starttime ASC) nextclub
FROM names n
JOIN races r ON r.id = n.raceid
JOIN classes cl ON cl.id = n.classid
WHERE r.id = %s
  AND n.starttime IS NOT NULL
) a
WHERE a.club = a.prevclub
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]




def read_race(conn_mgr, raceid):
    logging.info("read_race: %s", raceid)
    conn = conn_mgr.get_connection()

    cursor = conn.cursor()
    sql = """
SELECT r.id, r.name, r.racedate, r.svr_first_start, r.svr_drawplan_changed, r.svr_draw_time
FROM races r 
WHERE r.id = %s
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_not_planned(conn_mgr, raceid):
    logging.info("sql.read_not_planned, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT cl.id classid, cl.name Klasse
     , (SELECT COUNT(id) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X')) Ant
     , co.`name` Løype
     , SUBSTRING_INDEX(co.codes," ",1) Post_1
FROM classes cl
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
WHERE cl.raceid = %s AND cl.cource = 0
  AND NOT EXISTS(
      SELECT cl.id
	  FROM svr_classstarts cls
	  WHERE cls.classid = cl.id
     UNION
      SELECT cl.id
	  FROM svr_classstarts_not clsn
	  WHERE clsn.classid = cl.id)
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_block_lags(conn_mgr, raceid):
    logging.info("sql.read_block_lags, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT bll.id blocklagid, bl.id blockid, bl.name Bås, bll.timelag Slep, bll.timegap Gap
   ,(
	SELECT max(t.nexttime) Neste FROM (
	SELECT nexttime FROM svr_classstarts cls WHERE cls.blocklagid =  bll.id
	UNION
	SELECT svr_first_start nexttime FROM races WHERE id = %s
	) t   ) Neste
    , NULL Ledig
FROM svr_startblocklags bll
JOIN svr_startblocks bl ON bl.id = bll.startblockid AND bl.raceid = %s
"""
    cursor.execute(sql, (raceid, raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_class_starts(conn_mgr, raceid):
    logging.info("sql.read_class_starts, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT cls.id classstartid, sbl.id blocklagid, sb.name Bås, sbl.timelag Slep, cls.sortorder
      , cl.name Klasse
      , co.name Løype
      , SUBSTRING_INDEX(co.codes," ",1) Post_1
      , cls.timegap Gap
      , (SELECT COUNT(id) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X')) Antall
      , cls.freebefore Ant_før
      , cls.freeafter Ant_bak
      , cls.classstarttime Starttid
      , cls.nexttime Nestetid
FROM svr_classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN svr_startblocklags sbl ON sbl.id = cls.blocklagid
JOIN svr_startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
ORDER BY  sb.name, sbl.timelag, cls.sortorder 
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def upd_first_start(conn_mgr, raceid, new_value):
    logging.info("sql.upd_first_start, raceid: %s", raceid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE races
set svr_first_start = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, raceid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def upd_drawplan_changed(conn_mgr, raceid, new_value):
    logging.info("sql.upd_drawplan_changed, raceid: %s", raceid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE races
set svr_drawplan_changed = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, raceid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def upd_draw_time(conn_mgr, raceid, new_value):
    logging.info("sql.upd_draw_time, raceid: %s", raceid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE races
set svr_draw_time = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, raceid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


"""
 Rebuild the redundent fields (sortorder, qtybefore, classstarttime, nexttime).
"""
def rebuild_class_starts(conn_mgr, raceid):
    logging.info("sql.rebuild_class_starts, raceid: %s", raceid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
WITH classst AS (
SELECT classstartid, classname, cource, control1, blocklagid, sbname, timelag, timegap, sortorder
     , noinclass, freebefore, freeafter, newsortorder, basetime
     , LAG(COALESCE(spansqty,0)) OVER (ORDER BY sortorder) qtybefore
     , COALESCE(spansqty,0) spansqty
     , DATE_ADD(basetime, INTERVAL COALESCE(
		     LAG(COALESCE(spansqty,0)) OVER (PARTITION BY blocklagid ORDER BY sortorder),0)
			  *timegap SECOND) classstarttime
     , DATE_ADD(basetime, INTERVAL COALESCE(spansqty,0)
			  *timegap SECOND) nexttime
FROM (
SELECT cls.id classstartid, cl.name classname
      , co.name cource
      , SUBSTRING_INDEX(co.codes," ",1) control1
      , sbl.id blocklagid, sb.name sbname, sbl.timelag, cls.timegap, cls.sortorder 
      , (SELECT COUNT(id) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X')) noinclass -- Avmeldt, Arrangør
		, COALESCE(cls.freebefore,0) freebefore, COALESCE(cls.freeafter,0) freeafter
		, (ROW_NUMBER() OVER (order BY sb.name, sbl.timelag, cls.sortorder))*10 newsortorder
      , DATE_ADD( r.svr_first_start, INTERVAL sbl.timelag SECOND) basetime
      , SUM((SELECT COUNT(*) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X'))+COALESCE(cls.freebefore,0)+COALESCE(cls.freeafter,0)) OVER (PARTITION BY sbl.id ORDER BY cls.sortorder) spansqty
FROM svr_classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN svr_startblocklags sbl ON sbl.id = cls.blocklagid
JOIN svr_startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
ORDER BY cls.sortorder
) t1
)
UPDATE svr_classstarts stcl2
JOIN classst ON classst.classstartid = stcl2.id
SET stcl2.sortorder = classst.newsortorder
   ,stcl2.classstarttime = classst.classstarttime
   ,stcl2.nexttime = classst.nexttime
   ,stcl2.qtybefore = COALESCE(classst.qtybefore, 0)
"""
        cursor.execute(sql, (raceid,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def rebuild_class_starts_partition(conn_mgr, raceid, blocklagid):
    logging.info("sql.rebuild_class_starts_partition, blocklagid %s", blocklagid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
--
-- Rebuild the redundent fields (sortorder, qtybefore, classstarttime, nexttime).
--
WITH classst AS (
SELECT classstartid, classname, cource, control1, blocklagid, sbname, timelag, timegap, sortorder
     , noinclass, freebefore, freeafter, newsortorder, basetime
     , LAG(COALESCE(spansqty,0)) OVER (ORDER BY sortorder) qtybefore
     , COALESCE(spansqty,0) spansqty
     , DATE_ADD(basetime, INTERVAL COALESCE(
		     LAG(COALESCE(spansqty,0)) OVER (PARTITION BY blocklagid ORDER BY sortorder),0)
			  *timegap SECOND) classstarttime
     , DATE_ADD(basetime, INTERVAL COALESCE(spansqty,0)
			  *timegap SECOND) nexttime
FROM (
SELECT cls.id classstartid, cl.name classname
      , co.name cource
      , SUBSTRING_INDEX(co.codes," ",1) control1
      , sbl.id blocklagid, sb.name sbname, sbl.timelag, cls.timegap, cls.sortorder 
      , (SELECT COUNT(id) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X')) noinclass -- Avmeldt, Arrangør
		, COALESCE(cls.freebefore,0) freebefore, COALESCE(cls.freeafter,0) freeafter
		, (ROW_NUMBER() OVER (order BY cls.sortorder))*10 newsortorder
      , DATE_ADD( r.svr_first_start, INTERVAL sbl.timelag SECOND) basetime
      , SUM((SELECT COUNT(*) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X'))+COALESCE(cls.freebefore,0)+COALESCE(cls.freeafter,0)) OVER (PARTITION BY sbl.id ORDER BY cls.sortorder) spansqty
FROM svr_classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN svr_startblocklags sbl ON sbl.id = cls.blocklagid
JOIN svr_startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
  AND sbl.id = %s
ORDER BY cls.sortorder 
) t1
)
UPDATE svr_classstarts stcl2
JOIN classst ON classst.classstartid = stcl2.id
SET stcl2.sortorder = classst.newsortorder
   ,stcl2.classstarttime = classst.classstarttime
   ,stcl2.nexttime = classst.nexttime
   ,stcl2.qtybefore = COALESCE(classst.qtybefore, 0)
"""
        cursor.execute(sql, (raceid,blocklagid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def delete_class_start_row(conn_mgr, race_id, classstart_id):
    logging.info("sql.delete_class_start_row, id: %s", classstart_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_classstarts WHERE id = %s
    """
        cursor.execute(sql, (classstart_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def delete_class_start_rows(conn_mgr, race_id, blocklag_id):
    logging.info("sql.delete_class_start_rows, blocklagid: %s", blocklag_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_classstarts WHERE blocklagid = %s
    """
        cursor.execute(sql, (blocklag_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def delete_class_start_all(conn_mgr, race_id):
    logging.info("sql.delete_class_start_all, raceid: %s", race_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_classstarts cls
WHERE cls.classid in (
SELECT cl.id
FROM classes cl
JOIN races r ON r.id = cl.raceid
WHERE cl.cource = 0
  AND r.id = %s
)
"""
        cursor.execute(sql, (race_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


def delete_blocklag(conn_mgr, race_id, blocklag_id):
    logging.info("sql.delete_blocklag, blocklag_id: %s", blocklag_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_startblocklags sbl
WHERE sbl.id = %s
  AND NOT EXISTS (SELECT NULL FROM svr_classstarts cs WHERE  cs.blocklagid = sbl.id)
"""
        cursor.execute(sql, (blocklag_id, ))
        if cursor.rowcount > 0:
            to_return = True
        else:
            to_return = False
        conn.commit()
        conn.close()
        return to_return
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def delete_block(conn_mgr, race_id, blockId):
    logging.info("sql.delete_block, blockId: %s", blockId)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_startblocks sb
WHERE sb.id = %s
  AND NOT EXISTS (SELECT NULL FROM svr_startblocklags sbl WHERE  sbl.startblockid = sb.id)
"""
        cursor.execute(sql, (blockId, ))
        if cursor.rowcount > 0:
            to_return = True
        else:
            to_return = False
        conn.commit()
        conn.close()
        return to_return
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def insert_class_start_not(conn_mgr, race_id, class_id):
    logging.info("sql.insert_class_start_not, class_id: %s", class_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO svr_classstarts_not (classid)
    VALUES (%s)
"""
        cursor.execute(sql, (class_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def delete_class_start_not(conn_mgr, race_id):
    logging.info("sql.delete_class_start_not, race_id: %s", race_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM svr_classstarts_not csn
WHERE csn.classid in ( 
   SELECT cl.id
   FROM classes cl 
   WHERE cl.id = csn.classid
	 AND cl.raceid = %s
)
"""
        cursor.execute(sql, (race_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def insert_class_start(conn_mgr, race_id, blocklag_id, class_id, timegap, sortorder):
    logging.info("sql.insert_class_start, blocklag_id: %s, class_id: %s", blocklag_id, class_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO svr_classstarts (blocklagid, classid, timegap, sortorder)
    VALUES (%s, %s, %s, %s)
"""
        cursor.execute(sql, (blocklag_id, class_id, timegap, sortorder))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


def add_block(conn_mgr, race_id, block):
    logging.info("sql.add_block, block: %s", block)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO svr_startblocks (raceid, name)
VALUES (%s, %s)
"""
        cursor.execute(sql, (race_id, block))
        ny_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return ny_id
    except pymysql.IntegrityError as err:
        if err.args[0] == 1062:
            raise MyCustomError("Bås med det navnet finnes fra før!")
        else:
            logging.error(f"MySQL-feil: {err}")
            raise
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


def add_blocklag(conn_mgr, blockid, lag, gap):
    logging.info("sql.add_blocklag, blockid: %s, lag: %s, gap: %s", blockid, lag, gap)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO svr_startblocklags (startblockid, timelag, timegap)
VALUES (%s, %s, %s)
"""
        cursor.execute(sql, (blockid, lag, gap))
        conn.commit()
        ny_id = cursor.lastrowid
        conn.close()
        return ny_id
    except pymysql.IntegrityError as err:
        if err.args[0] == 1062:
            logging.error(f"MySQL-feil: {err}")
            raise MyCustomError("Denne kombinasjonen av Bås/tidsslep finnes fra før!")
        else:
            logging.error(f"MySQL-feil: {err}")
            raise
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


def upd_class_start_free_before(conn_mgr, race_id, classstartid, new_value):
    logging.info("sql.upd_class_start_free_before, classstartid: %s, new_value: %s", classstartid, new_value)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE svr_classstarts
set freebefore = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, classstartid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def upd_class_start_free_after(conn_mgr, race_id, classstartid, new_value):
    logging.info("sql.upd_class_start_free_after, classstartid: %s, new_value: %s", classstartid, new_value)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE svr_classstarts
set freeafter = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, classstartid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def sql_start_list(conn_mgr, raceid):
    logging.info("sql.sql_start_list, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT cl.name klasse, n.startnr , n.name navn, n.club, n.ecardno brikke, concat("&nbsp;&nbsp;&nbsp;&nbsp;", substring(cast(n.starttime as char),12,8)) starttid
FROM names n
JOIN classes cl on cl.id = n.classid
JOIN races r on r.id = cl.raceid
WHERE r.id = %s
  AND n.status not in ('V','X')
ORDER BY cl.sortorder, n.starttime
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def sql_starter_list(conn_mgr, raceid):
    logging.info("sql.sql_starter_list, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT n.startnr , n.name navn, n.club, n.ecardno brikke, cl.name klasse
     , concat("_____________________________________________________________________", substring(cast(n.starttime as char),12,8)) starttid
     ,'&#x25A1;' html_kvadrat
FROM names n
JOIN classes cl on cl.id = n.classid
JOIN races r on r.id = cl.raceid
WHERE r.id = %s
  AND n.status not in ('V','X')
  AND n.starttime is not null
ORDER BY n.starttime, cl.sortorder
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def sql_noof_in_cource(conn_mgr, raceid):
    logging.info("sql.sql_noof_in_cource, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT distinct
  concat(r.name, ", totalt: ", COUNT(n.NAME) OVER (PARTITION BY r.id), "<br>Løype______________________Antall")
 ,co.name Løype
 ,COUNT(n.NAME) OVER (PARTITION BY co.name) Antall 
FROM names n 
JOIN races r ON r.id = n.raceid
JOIN classes cl ON cl.id = n.classid AND cl.id not in (select classid from svr_classstarts_not)
JOIN classcource cc ON cc.raceid = r.id AND cc.classid = cl.id AND cc.auto_cource_recognition = 0
JOIN classes co ON co.id = cc.courceid AND co.cource = 1
WHERE r.id = %s
  and n.status NOT IN ('V','X')
ORDER BY Antall desc
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def sql_noof_in_control1(conn_mgr, raceid):
    logging.info("sql.sql_noof_in_control1, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT distinct
  concat(r.name, ", totalt: ", COUNT(n.NAME) OVER (PARTITION BY r.id), "<br>Post1__Antall____Løype__________Antall")
 ,SUBSTRING_INDEX(co.codes,' ',1) Post1
 ,COUNT(n.NAME) OVER (PARTITION BY SUBSTRING_INDEX(co.codes,' ',1)) Ant_post1
 ,co.name Løype
 ,COUNT(n.NAME) OVER (PARTITION BY co.name) Ant_løype
FROM names n 
JOIN races r ON r.id = n.raceid
JOIN classes cl ON cl.id = n.classid AND cl.id not in (select classid from svr_classstarts_not)
JOIN classcource cc ON cc.raceid = r.id AND cc.classid = cl.id AND cc.auto_cource_recognition = 0
JOIN classes co ON co.id = cc.courceid AND co.cource = 1
WHERE r.id = %s
  and n.status NOT IN ('V','X')
ORDER BY Ant_post1 desc, Ant_løype desc
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

#
# Samtidig startende til samme post1
#
def sql_same_time_control1(conn_mgr, raceid):
    logging.info("sql.sql_same_time_control1, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT time(n.starttime) Starttid
     , SUBSTRING_INDEX(co2.codes,' ',1) Post_1
     , COUNT(n.NAME) Samtidige
FROM names n
JOIN races r ON r.id = n.raceid
JOIN classes cl ON cl.id = n.classid
JOIN classcource cc ON cc.raceid = r.id AND cc.classid = cl.id AND cc.auto_cource_recognition = 0
JOIN classes co2 ON co2.id = cc.courceid AND co2.cource = 1
WHERE r.id = %s
  AND n.starttime IS NOT null
GROUP BY Starttid, Post_1
HAVING COUNT(n.NAME) > 1
ORDER BY Starttid, Post_1
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

#
# Samtidig startende i samme løype
#
def sql_same_time_cource(conn_mgr, raceid):
    logging.info("sql.sql_same_time_cource, raceid: %s", raceid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT time(n.starttime) Starttid
     , co2.name Løype
     , COUNT(n.NAME) Samtidige
FROM names n
JOIN races r ON r.id = n.raceid
JOIN classes cl ON cl.id = n.classid
JOIN classcource cc ON cc.raceid = r.id AND cc.classid = cl.id AND cc.auto_cource_recognition = 0
JOIN classes co2 ON co2.id = cc.courceid AND co2.cource = 1
WHERE r.id = %s
  AND n.starttime IS NOT null
GROUP BY Starttid, Løype
HAVING COUNT(n.NAME) > 1
ORDER BY Starttid, Løype
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


def clear_start_times(conn_mgr, race_id):
    logging.info("sql.clear_start_times, raceid: %s", race_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
WITH n1 AS (
	SELECT n.id, n.raceid, n.classid, cl.name classname, n.name, r.racedate
	FROM names n 
	JOIN classes cl ON cl.id = n.classid AND cl.cource = 0 
	JOIN svr_classstarts cls ON cls.classid = cl.id
	JOIN races r ON r.id = n.raceid AND n.status NOT IN ('V','X') AND r.id = %s
)
UPDATE names n
JOIN n1 ON n.id = n1.id
SET n.starttime = null
"""
        cursor.execute(sql, (race_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def draw_start_times(conn_mgr, race_id):
    logging.info("sql.draw_start_times, race_id: %s", race_id)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
WITH n1 AS (
SELECT n.id, n.raceid, n.classid, cl.name classname, n.name, r.racedate
	      ,ROW_NUMBER() OVER(PARTITION BY cls.id ORDER BY RAND())-1+COALESCE(cls.freebefore, 0) nowithinclass
	      ,cls.classstarttime, cls.timegap 
	FROM names n 
	JOIN classes cl ON cl.id = n.classid AND cl.cource = 0 
	JOIN svr_classstarts cls ON cls.classid = cl.id
	JOIN races r ON r.id = n.raceid AND n.status NOT IN ('V','X') AND r.id = %s
)
UPDATE names n
JOIN n1 ON n.id = n1.id
SET n.starttime = DATE_ADD(n1.classstarttime, INTERVAL nowithinclass*n1.timegap SECOND)
"""
        cursor.execute(sql, (race_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

#
# Trekk starttider for ei klasse
#
def draw_start_times_class(conn_mgr, classid):
    logging.info("sql.draw_start_times_class, class_id: %s", classid)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
WITH n1 AS (
SELECT n.id, n.raceid, n.classid, cl.name classname, n.name, r.racedate
	      ,ROW_NUMBER() OVER(PARTITION BY cls.id ORDER BY RAND())-1+COALESCE(cls.freebefore, 0) nowithinclass
	      ,cls.classstarttime, cls.timegap 
	FROM names n 
	JOIN classes cl ON cl.id = n.classid AND cl.cource = 0 AND classid = %s
	JOIN svr_classstarts cls ON cls.classid = cl.id
	JOIN races r ON r.id = n.raceid AND n.status NOT IN ('V','X')
)
UPDATE names n
JOIN n1 ON n.id = n1.id
SET n.starttime = DATE_ADD(n1.classstarttime, INTERVAL nowithinclass*n1.timegap SECOND)
"""
        cursor.execute(sql, (classid,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


"""
Alle løpere i gitt klasse, i start-rekkefølge.
"""
def read_names(conn_mgr, classid):
    logging.info("sql.read_names, classid: %s", classid)
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT n.id, n.classid, cl.name Klasse, n.name Løper, n.club Klubb, n.starttime Starttid
FROM NAMES n
JOIN classes cl on cl.id = n.classid and cl.cource = 0
WHERE n.classid = %s
  AND n.starttime is not null
ORDER BY n.starttime
"""
    cursor.execute(sql, (classid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def class_start_down_up(conn_mgr, id, step):
    logging.info("sql.class_start_up_down: %s, %s", id, step)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE svr_classstarts clss
set sortorder = sortorder + %s
WHERE id = %s
"""
        cursor.execute(sql, (step, id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise



def swap_start_times(conn_mgr, id1, id2, race_id):
    logging.info("sql.swap_start_times: %s, %s", id1, id2)
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
with n1 as (
select n.id, n.name, n.club, n.starttime
 , ifnull(LAG(n.starttime) OVER (ORDER BY n.starttime ASC), LEAD(n.starttime) OVER (ORDER BY n.starttime ASC)) othertime
from names n
where n.id in 
(%s,%s)
  and n.raceid = %s -- dobeltsikring mot å skrive feil id. Langdistanse.
)
update names n2
join n1 on n1.id = n2.id
set n2.starttime = n1.othertime
"""
        cursor.execute(sql, (id1, id2, race_id,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise


#
# Sjekk om database objektene til Trekkeplan er installert.
#
def is_db_objects_installed(conn_mgr):
    logging.info("sql.is_db_objects_installed")
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
SHOW COLUMNS FROM races LIKE 'svr_first_start'
"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        row_count = len(rows)
        return row_count > 0
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise

def install_db_objects(conn_mgr):
    logging.info("sql.install_db_objects")
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = "ALTER TABLE races ADD COLUMN svr_first_start DATETIME"
        cursor.execute(sql)
        sql = "ALTER TABLE races ADD COLUMN svr_draw_time DATETIME"
        cursor.execute(sql)
        sql = "ALTER TABLE races ADD COLUMN svr_drawplan_changed DATETIME"
        cursor.execute(sql)
        sql = """
CREATE TABLE `svr_startblocks` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`raceid` INT NOT NULL,
	`name` VARCHAR(80) NOT NULL DEFAULT '',
	PRIMARY KEY (`id`),
	UNIQUE INDEX `name` (`name` ASC, `raceid` ASC)
)
AUTO_INCREMENT=1
"""
        cursor.execute(sql)
        sql = """
CREATE TABLE `svr_startblocklags` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`startblockid` INT NULL DEFAULT NULL,
	`timelag` INT NULL DEFAULT NULL,
	`timegap` INT NULL DEFAULT NULL,
	PRIMARY KEY (`id`),
	UNIQUE INDEX `startblockid_lag` (`startblockid`, `timelag`)
)
AUTO_INCREMENT=1
    """
        cursor.execute(sql)
        sql = """
 CREATE TABLE `svr_classstarts` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`blocklagid` INT NOT NULL,
	`classid` INT NOT NULL,
	`timegap` INT NULL DEFAULT NULL,
	`freebefore` INT NULL DEFAULT NULL,
	`freeafter` INT NULL DEFAULT NULL,
	`sortorder` INT NOT NULL,
	`qtybefore` INT NULL DEFAULT NULL,
	`classstarttime` DATETIME NULL DEFAULT NULL,
	`nexttime` DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (`id`),
	UNIQUE INDEX `classid` (`classid`)
)
AUTO_INCREMENT=1
"""
        cursor.execute(sql)
        sql = """
CREATE TABLE `svr_classstarts_not` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`classid` INT NOT NULL,
	PRIMARY KEY (`id`),
	UNIQUE INDEX `classid` (`classid`)
)
AUTO_INCREMENT=1
"""
        cursor.execute(sql)
        logging.info("Database objects installed!")

    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
        raise
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
        raise
