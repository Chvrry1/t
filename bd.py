import psycopg2


def obtener_conexion():
    conn = psycopg2.connect(
        host="localhost",
        database="tesis",
        user="postgres",
        password="admin")
    return conn

class SecretKey():
    JWT_SECRET_KEY = 'hmeraSecretKey$01++'