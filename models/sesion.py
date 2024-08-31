import datetime
import hashlib
import json

import jwt

from bd import obtener_conexion as db

JWT_SECRET = 'hola'
class MD5Hash:
    @staticmethod
    def md5_password(password):
        pwdBytes = password.encode(encoding='UTF-8', errors='strict')
        h = hashlib.md5()
        h.update(pwdBytes)
        return h.hexdigest()
class Sesion():

    def iniciarSesion(self, nombre, clave):
        # Abrir una conexión a la BD
        con = db()

        # Crear un cursor para almacenar los datos que devuelve la consulta SQL
        cursor = con.cursor()

        # Preparar la consulta SQL para validar las credenciales
        sql = """SELECT 
                            usuario_id, 
                            nombre,
                            clave,
                            estado_usuario
                        FROM 
                            usuarios 
                        WHERE 
                            nombre = %s"""

        # Ejecutar la consulta SQL
        cursor.execute(sql, (nombre,))

        # Almacenar los datos que devuelve la consulta SQL
        datos = cursor.fetchone()

        # Verificar que 'datos' no sea None y que contenga los índices esperados
        if datos and len(datos) >= 4:  # Validar si la variable "datos" contiene registros y el índice esperado
            hashed_password = MD5Hash.md5_password(clave)
            if hashed_password == datos[2]:  # Comparar la contraseña hash
                if datos[3] == '1':  # Estado: Activo
                    # Crear token JWT
                    token = jwt.encode({
                        'user_id': datos[0],
                        'user': datos[1],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                    }, JWT_SECRET, algorithm='HS256')

                    # Registrar inicio de sesión en log_sesiones
                    usuario_id = datos[0]
                    try:
                        cursor.execute("INSERT INTO log_sesiones (usuario_id) VALUES (%s)", (usuario_id,))
                        con.commit()
                    except Exception as e:
                        print(f"Error al registrar sesión: {e}")
                        return False, 'Error al registrar sesión'

                    # Cerrar el cursor y la conexión a la BD
                    cursor.close()
                    con.close()

                    return True, token
                else:  # Estado: Inactivo
                    cursor.close()
                    con.close()
                    return False, 'Cuenta inactiva. Consulte con su administrador'
            else:
                cursor.close()
                con.close()
                return False, 'El usuario no existe o sus credenciales son incorrectas'
        else:  # No hay datos
            cursor.close()
            con.close()
            return False, 'El usuario no existe o sus credenciales son incorrectas'

    def actualizarToken(self, token, usuarioID):
        # Abrir conexión a la BD
        con = db()

        # Configurar para que los cambios de escritura en la BD se confirmen de manera manual
        con.autocommit = False

        # Crear un cursor
        cursor = con.cursor()

        # Preparar la sentencia para actualizar el token
        sql = "update usuario set token=%s, estado_token='1' where id=%s"

        try:
            # Ejecutar la sentencia sql
            cursor.execute(sql, [token, usuarioID])

            # Confirmar la sentencia de actualización
            con.commit()

        except con.Error as error:
            # Revocar la operación en la base de datos
            con.rollback()
        finally:
            cursor.close()
            con.close()

    def registrar(self, nombre, password):
        # Abrir conexión a la BD
        con = db()

        # Crear un cursor
        cursor = con.cursor()

        # Verificar si el nombre de usuario ya existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nombre = %s", (nombre,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            con.close()
            return False, 'El nombre de usuario ya está en uso.'

        # Encriptar la contraseña
        hashed_password = MD5Hash.md5_password(password)

        try:
            cursor.execute("INSERT INTO usuarios (nombre, clave, estado_usuario) VALUES (%s, %s, '0')", (nombre, hashed_password))
            con.commit()
            return True, 'Usuario registrado exitosamente'
        except Exception as e:
            con.rollback()
            print(f"Error al registrar usuario: {e}")
            return False, 'Error al registrar usuario'
        finally:
            cursor.close()
            con.close()

    def validarEstadoToken(self, usuarioID):
        # Abrir una conexión a la BD
        con = db()

        # Crear un cursor para almacenar los datos que devuelve la consulta SQL
        cursor = con.cursor()

        # Preparar la consulta SQL para validar las credenciales
        sql = "select estado_token from usuario where id=%s"

        # Ejecutar la consulta SQL
        cursor.execute(sql, [usuarioID])

        # Almacenar los datos que devuelve la consulta SQL
        datos = cursor.fetchone()

        # Cerrar el cursor y la conexión a la BD
        cursor.close()
        con.close()

        if datos:
            return json.dumps({'status': True, 'data': datos, 'message': 'Estado de token'})
        else:
            return json.dumps({'status': False, 'data': None, 'message': 'Estado de token no encontrado'})