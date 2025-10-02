def readNotPlanned(conn, raceid):
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
#    rows = cursor.fetchall()
    return cursor.fetchall(), [desc[0] for desc in cursor.description]
