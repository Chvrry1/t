from bd import obtener_conexion
def obtener_camaras():
    conexion = obtener_conexion()
    camaras = []
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM camaras where estado = '1'")
        camaras = cursor.fetchall()
    conexion.close()
    return camaras
