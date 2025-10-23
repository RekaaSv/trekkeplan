import logging

import pymysql
from control.errors import MyCustomError

def read_race_list(conn_mgr):
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT r.racedate Dag, r.name Løp, TIME(r.first_start) Starttid, r.id
FROM races r
ORDER BY r.created DESC
"""
    cursor.execute(sql)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

"""
Løpere som har klubbkamerat i samme klasse rett før.
"""
def read_club_mates(conn_mgr, raceid):
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT a.id, a.previd, a.classid
     , a.classname Klasse, a.name Løper, a.club Klubb, time(a.starttime) Starttid FROM
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
    logging.info("read_race", raceid)
    conn = conn_mgr.get_connection()

    cursor = conn.cursor()
    sql = """
SELECT r.id, r.name, r.racedate, r.first_start
FROM races r 
WHERE r.id = %s
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_not_planned(conn_mgr, raceid):
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
	  FROM classstarts cls
	  WHERE cls.classid = cl.id
     UNION
      SELECT cl.id
	  FROM classstarts_not clsn
	  WHERE clsn.classid = cl.id)
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_block_lags(conn_mgr, raceid):
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT bll.id blocklagid, bl.id blockid, bl.name Bås, bll.timelag Slep, bll.timegap Gap
   ,(select max(nexttime) from classstarts cls where cls.blocklagid = bll.id) Neste 
FROM startblocklags bll
JOIN startblocks bl ON bl.id = bll.startblockid AND bl.raceid = %s"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_block_lag(conn_mgr, blocklagid):
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT bll.id blocklagid, bl.id blockid, bl.name Bås, bll.timelag Slep, bll.timegap Gap
   ,(select max(nexttime) from classstarts cls where cls.blocklagid = bll.id) Neste 
FROM startblocklags bll
JOIN startblocks bl ON bl.id = bll.startblockid AND bll.id = %s
"""
    cursor.execute(sql, (blocklagid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]


def read_class_starts(conn_mgr, raceid):
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
FROM classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN startblocklags sbl ON sbl.id = cls.blocklagid
JOIN startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
ORDER BY  sb.name, sbl.timelag, cls.sortorder 
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def upd_first_start(conn_mgr, raceid, new_value):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE races
set first_start = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, raceid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

"""
 Rebuild the redundent fields (sortorder, qtybefore, classstarttime, nexttime).
"""
def rebuild_class_starts(conn_mgr, raceid):
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
      , DATE_ADD( r.first_start, INTERVAL sbl.timelag SECOND) basetime
      , SUM((SELECT COUNT(*) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X'))+COALESCE(cls.freebefore,0)+COALESCE(cls.freeafter,0)) OVER (PARTITION BY sbl.id ORDER BY cls.sortorder) spansqty
FROM classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN startblocklags sbl ON sbl.id = cls.blocklagid
JOIN startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
ORDER BY cls.sortorder
) t1
)
UPDATE classstarts stcl2
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
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def rebuild_class_starts_partition(conn_mgr, raceid, blocklagid):
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
      , DATE_ADD( r.first_start, INTERVAL sbl.timelag SECOND) basetime
      , SUM((SELECT COUNT(*) FROM names n WHERE n.classid = cl.id AND n.status NOT IN ('V','X'))+COALESCE(cls.freebefore,0)+COALESCE(cls.freeafter,0)) OVER (PARTITION BY sbl.id ORDER BY cls.sortorder) spansqty
FROM classstarts cls
JOIN classes cl ON cl.cource = 0 AND cl.id = cls.classid
LEFT JOIN classcource cc ON cc.auto_cource_recognition = 0 AND cc.classid = cl.id
LEFT JOIN classes co ON co.id = cc.courceid 
JOIN races r ON r.id = cl.raceid
JOIN startblocklags sbl ON sbl.id = cls.blocklagid
JOIN startblocks sb ON sb.id = sbl.startblockid
WHERE r.id = %s
  AND sbl.id = %s
ORDER BY cls.sortorder 
) t1
)
UPDATE classstarts stcl2
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
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def delete_class_start_row(conn_mgr, raceId, classstartId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM classstarts WHERE id = %s
    """
        cursor.execute(sql, (classstartId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def delete_class_start_rows(conn_mgr, raceId, blocklagId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM classstarts WHERE blocklagid = %s
    """
        cursor.execute(sql, (blocklagId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def delete_class_start_all(conn_mgr, raceId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM classstarts cls
WHERE cls.classid in (
SELECT cl.id
FROM classes cl
JOIN races r ON r.id = cl.raceid
WHERE cl.cource = 0
  AND r.id = %s
)
"""
        cursor.execute(sql, (raceId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")


def delete_blocklag(conn_mgr, raceId, blocklagId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM startblocklags sbl
WHERE sbl.id = %s
  AND NOT EXISTS (SELECT NULL FROM classstarts cs WHERE  cs.blocklagid = sbl.id)
"""
        cursor.execute(sql, (blocklagId, ))
        if cursor.rowcount > 0:
            to_return = True
        else:
            to_return = False
        conn.commit()
        conn.close()
        return to_return
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def delete_block(conn_mgr, raceId, blockId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM startblocks sb
WHERE sb.id = %s
  AND NOT EXISTS (SELECT NULL FROM startblocklags sbl WHERE  sbl.startblockid = sb.id)
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
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def insert_class_start_not(conn_mgr, raceId, classId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO classstarts_not (classid)
    VALUES (%s)
"""
        cursor.execute(sql, (classId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def delete_class_start_not(conn_mgr, raceId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
DELETE FROM classstarts_not csn
WHERE csn.classid in ( 
   SELECT cl.id
   FROM classes cl 
   WHERE cl.id = csn.classid
	 AND cl.raceid = %s
)
"""
        cursor.execute(sql, (raceId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def insert_class_start(conn_mgr, raceId, blocklagId, classId, timegap, sortorder):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO classstarts (blocklagid, classid, timegap, sortorder)
    VALUES (%s, %s, %s, %s)
"""
        cursor.execute(sql, (blocklagId, classId, timegap, sortorder))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")


def add_block(conn_mgr, raceId, block):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO startblocks (raceid, name)
VALUES (%s, %s)
"""
        cursor.execute(sql, (raceId, block))
        ny_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return ny_id
    except pymysql.IntegrityError as err:
        if err.args[0] == 1062:
            raise MyCustomError("Bås med det navnet finnes fra før!")
        else:
            logging.error(f"MySQL-feil: {err}")
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")


def add_blocklag(conn_mgr, blockid, lag, gap):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
INSERT INTO startblocklags (startblockid, timelag, timegap)
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
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")


def upd_class_start_free_before(conn_mgr, raceId, classstartid, new_value):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE classstarts
set freebefore = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, classstartid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def upd_class_start_free_after(conn_mgr, raceId, classstartid, new_value):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE classstarts
set freeafter = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, classstartid))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def sql_start_list(conn_mgr, raceid):
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
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def sql_starter_list(conn_mgr, raceid):
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
ORDER BY n.starttime, cl.sortorder
"""
    try:
        cursor.execute(sql, (raceid,))
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")


def clear_start_times(conn_mgr, raceId):
    try:
        conn = conn_mgr.get_connection()
        cursor = conn.cursor()
        sql = """
WITH n1 AS (
	SELECT n.id, n.raceid, n.classid, cl.name classname, n.name, r.racedate
	FROM names n 
	JOIN classes cl ON cl.id = n.classid AND cl.cource = 0 
	JOIN classstarts cls ON cls.classid = cl.id
	JOIN races r ON r.id = n.raceid AND n.status NOT IN ('V','X') AND r.id = %s
)
UPDATE names n
JOIN n1 ON n.id = n1.id
SET n.starttime = null
"""
        cursor.execute(sql, (raceId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

def draw_start_times(conn_mgr, raceId):
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
	JOIN classstarts cls ON cls.classid = cl.id
	JOIN races r ON r.id = n.raceid AND n.status NOT IN ('V','X') AND r.id = %s
)
UPDATE names n
JOIN n1 ON n.id = n1.id
SET n.starttime = DATE_ADD(n1.classstarttime, INTERVAL nowithinclass*n1.timegap SECOND)
"""
        cursor.execute(sql, (raceId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")

"""
Alle løpere i gitt klasse, i start-rekkefølge.
"""
def read_names(conn_mgr, classid):
    conn = conn_mgr.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT n.id, n.classid, cl.name Klasse, n.name Løper, n.club Klubb, time(n.starttime) Starttid
FROM NAMES n
JOIN classes cl on cl.id = n.classid and cl.cource = 0
WHERE n.classid = %s
  AND n.starttime is not null
ORDER BY n.starttime
"""
    cursor.execute(sql, (classid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def swap_start_times(conn_mgr, id1, id2, raceId):
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
        cursor.execute(sql, (id1, id2, raceId,))
        conn.commit()
        conn.close()
    except pymysql.Error as err:
        logging.error(f"MySQL-feil: {err}")
    except Exception as e:
        logging.error(f"Uventet feil: {e}")
