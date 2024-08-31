from bd import obtener_conexion

def obtener_camaras():
    conexion = obtener_conexion()
    camaras = []
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM camaras")
        camaras = cursor.fetchall()
    conexion.close()
    return camaras


def obtener_num_reportes():
    query = "SELECT count(reporte_id) AS num FROM reportes"
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
        return result[0]
    finally:
        conn.close()


def obtener_num_registros():
    query = "select count(registro_id) as num from registros"
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
        return result[0]
    finally:
        conn.close()


def generar_reporte(camara_id, tiempo):
    query = generar_query_reportes(camara_id, tiempo)
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def generar_reporte_dias(camara_id, tiempo):
    query = generar_query_reportes_dias(camara_id, tiempo)
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def generar_reporte_dias_rango(camara_id, tiempo_i, tiempo_f):
    query = generar_query_reportes_dias_rango(camara_id, tiempo_i, tiempo_f)
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def generar_reporte_rango(camara_id, tiempo_i, tiempo_f):
    query = generar_query_reportes_rango(camara_id, tiempo_i, tiempo_f)
    conn = obtener_conexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def generar_query_reportes(camara_id, tiempo):
    query = f"""
        WITH horas AS (
            SELECT generate_series(0, 23) AS hora
        )
        SELECT LPAD(h.hora::text, 2, '0') || ':00' AS hora, 
               COALESCE(ROUND(AVG(num_registros)::numeric, 2), 0) AS promedio_incidencias 
        FROM horas h 
        LEFT JOIN (
            SELECT EXTRACT(HOUR FROM r.hora_inicio) AS hora, 
                   COUNT(r.registro_id) AS num_registros 
            FROM registros r 
            JOIN reportes rp ON r.reporte_id = rp.reporte_id 
            WHERE rp.fecha >= CURRENT_DATE - INTERVAL '{tiempo} days'
              AND rp.camara_id = {camara_id}
            GROUP BY hora
        ) AS subquery ON h.hora = subquery.hora 
        GROUP BY h.hora 
        ORDER BY h.hora
    """
    return query


def generar_query_reportes_dias(camara_id, tiempo):
    query = f"""
            WITH dias_semana AS (
                SELECT generate_series(0, 6) AS dia_semana
            )
            SELECT d.dia_semana AS dia, 
                   COALESCE(ROUND(AVG(num_registros)::numeric, 2), 0) AS promedio_incidencias 
            FROM dias_semana d
            LEFT JOIN (
                SELECT EXTRACT(DOW FROM rp.fecha) AS dia_semana, 
                       COUNT(r.registro_id) AS num_registros 
                FROM registros r 
                JOIN reportes rp ON r.reporte_id = rp.reporte_id 
                WHERE rp.fecha >= CURRENT_DATE - INTERVAL '{tiempo} days'
                  AND rp.camara_id = {camara_id}
                GROUP BY dia_semana
            ) AS subquery ON d.dia_semana = subquery.dia_semana 
            GROUP BY d.dia_semana 
            ORDER BY d.dia_semana;
    """
    return query


def generar_query_reportes_dias_rango(camara_id, tiempo_i, tiempo_f):
    query = f"""
            WITH dias_semana AS (
                SELECT generate_series(0, 6) AS dia_semana
            )
            SELECT d.dia_semana AS dia, 
                   COALESCE(ROUND(AVG(num_registros)::numeric, 2), 0) AS promedio_incidencias 
            FROM dias_semana d
            LEFT JOIN (
                SELECT EXTRACT(DOW FROM rp.fecha) AS dia_semana, 
                       COUNT(r.registro_id) AS num_registros 
                FROM registros r 
                JOIN reportes rp ON r.reporte_id = rp.reporte_id 
                WHERE rp.fecha >= '{tiempo_i}'::date
                  AND rp.fecha <= '{tiempo_f}'::date
                  AND rp.camara_id = {camara_id}
                GROUP BY dia_semana
            ) AS subquery ON d.dia_semana = subquery.dia_semana 
            GROUP BY d.dia_semana 
            ORDER BY d.dia_semana;

    """
    return query


def generar_query_reportes_rango(camara_id, tiempo_i, tiempo_f):
    query = f"""
        WITH horas AS (
            SELECT generate_series(0, 23) AS hora
        )
        SELECT LPAD(h.hora::text, 2, '0') || ':00' AS hora, 
               COALESCE(ROUND(AVG(num_registros)::numeric, 2), 0) AS promedio_incidencias 
        FROM horas h 
        LEFT JOIN (
            SELECT EXTRACT(HOUR FROM r.hora_inicio) AS hora, 
                   COUNT(r.registro_id) AS num_registros 
            FROM registros r 
            JOIN reportes rp ON r.reporte_id = rp.reporte_id 
            WHERE rp.fecha >= '{tiempo_i}'::date
              AND rp.fecha <= '{tiempo_f}'::date
              AND rp.camara_id = {camara_id}
            GROUP BY hora
        ) AS subquery ON h.hora = subquery.hora 
        GROUP BY h.hora 
        ORDER BY h.hora
    """
    return query
