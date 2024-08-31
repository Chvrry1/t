#***************************************
# Funcionalidad para validar el token
#***************************************

from ast import arg
from flask import jsonify, request, flash, redirect, url_for
from functools import wraps
from bd import SecretKey
import jwt
from models.sesion import Sesion
import json
JWT_SECRET = 'hola'

from flask import g

def validar(fx):
    @wraps(fx)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            flash('Se requiere iniciar sesión.')
            return redirect(url_for('login'))

        try:
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            g.nombre_usuario = decoded_token.get('user')  # Almacenar el nombre de usuario en g
        except jwt.ExpiredSignatureError:
            flash('Su sesión ha expirado. Por favor, inicie sesión nuevamente.')
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            flash('Token inválido. Por favor, inicie sesión nuevamente.')
            return redirect(url_for('login'))

        return fx(*args, **kwargs)

    return decorated
        

def validarEstadoTokenUsuario(usuarioID):
    obj = Sesion()
    resultadoJSON = obj.validarEstadoToken(usuarioID)
    resultadoJSONObject = json.loads(resultadoJSON)
    if resultadoJSONObject['status'] == True:
        estado_token_BD = resultadoJSONObject['data']['estado_token']
        if estado_token_BD == None:
            return False
        else:
            if estado_token_BD == '0': #Token inactivo
                return False
            else:
                return True
    else:
        return False


        