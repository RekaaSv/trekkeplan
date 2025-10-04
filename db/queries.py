import mysql.connector

from db import connection


def read_race(raceid):
    conn = connection.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT r.id, r.name, r.racedate, r.first_start
FROM races r 
WHERE r.id = %s
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_not_planned(raceid):
    conn = connection.get_connection()
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
  )
"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_block_lags(raceid):
    conn = connection.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT bll.id blocklagid, bl.id blockid, bl.name Bås, bll.timelag Slep
FROM startblocklags bll
JOIN startblocks bl ON bl.id = bll.startblockid AND bl.raceid = %s"""
    cursor.execute(sql, (raceid,))
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def read_class_starts(raceid):
    conn = connection.get_connection()
    cursor = conn.cursor()
    sql = """
SELECT cls.id classstartid, sbl.id blocklagid, sb.name Bås, sbl.timelag Slep
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

def upd_first_start(raceid, new_value):
    try:
        conn = connection.get_connection()
        cursor = conn.cursor()
        sql = """
UPDATE races
set first_start = %s
WHERE id = %s
"""
        cursor.execute(sql, (new_value, raceid))
        conn.commit()
        conn.close()
    except mysql.connector.Error as err:
        print(f"MySQL-feil: {err}")
    except Exception as e:
        print(f"Uventet feil: {e}")

def rebuild_class_starts(raceid):
    try:
        conn = connection.get_connection()
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
    except mysql.connector.Error as err:
        print(f"MySQL-feil: {err}")
    except Exception as e:
        print(f"Uventet feil: {e}")

def rebuild_class_starts_partition(raceid, blocklagid):
    try:
        conn = connection.get_connection()
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
    except mysql.connector.Error as err:
        print(f"MySQL-feil: {err}")
    except Exception as e:
        print(f"Uventet feil: {e}")
