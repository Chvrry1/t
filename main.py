import time
from datetime import datetime

import jwt
from validarToken import JWT_SECRET

from controllers import controlador_camaras, controlador_reportes
from flask import Flask, request, render_template, send_from_directory, redirect, jsonify, session, url_for, flash, g
import os
import threading
from detection.GarbageDetector import process_video
from models.sesion import Sesion
from validarToken import validar
from bd import obtener_conexion

app = Flask(__name__)
app.secret_key = 'seminarioDeTesis'

UPLOAD_FOLDER = 'static/input_videos/'
OUTPUT_FOLDER = 'static/out_videos/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

active_processes = {}


@app.route("/")
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['username']
        clave = request.form['password']
        sesion = Sesion()
        valido, mensaje_o_token = sesion.iniciarSesion(nombre, clave)
        if valido:
            session['username'] = nombre
            response = redirect(url_for('camaras'))
            response.set_cookie('token', mensaje_o_token)
            return response
        else:
            flash(mensaje_o_token)
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nombre = request.form['username']
        password = request.form['password']
        sesion = Sesion()
        valido, mensaje = sesion.registrar(nombre, password)
        flash(mensaje)
        if valido:
            return redirect(url_for('login'))
        else:
            return redirect(url_for('registrar'))
    return render_template('registrar.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    response = redirect(url_for('login'))
    response.delete_cookie('token')
    flash('Has cerrado sesión correctamente.')
    return response


@app.route("/gestion_usuarios")
@validar
def gestion_usuarios():
    if g.nombre_usuario != 'admin':
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('camaras'))

    con = obtener_conexion()
    cursor = con.cursor()
    cursor.execute("SELECT usuario_id, nombre, estado_usuario FROM usuarios WHERE nombre != 'admin'")
    usuarios = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("gestion_usuarios.html", usuarios=usuarios, nombre_usuario=g.nombre_usuario)


@app.route("/log_sesiones")
@validar
def log_sesiones():
    if g.nombre_usuario != 'admin':
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('camaras'))

    con = obtener_conexion()
    cursor = con.cursor()
    cursor.execute("""
                        SELECT 
                            l.usuario_id, 
                            u.nombre,
                            l.fecha_hora
                        FROM 
                            log_sesiones l
                        JOIN 
                            usuarios u 
                        ON 
                            l.usuario_id = u.usuario_id
                        ORDER BY 
                            l.log_sesion_id;
                        """)
    sesiones = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("log_sesiones.html", sesiones=sesiones, nombre_usuario=g.nombre_usuario)


@app.route("/log_archivos")
@validar
def log_archivos():
    if g.nombre_usuario != 'admin':
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('camaras'))

    con = obtener_conexion()
    cursor = con.cursor()
    cursor.execute("""
                    SELECT 
                        l.usuario_id, 
                        u.nombre,
                        l.nombre_archivo,
                        l.fecha_hora
                    FROM 
                        log_archivos l
                    JOIN 
                        usuarios u 
                    ON 
                        l.usuario_id = u.usuario_id
                    ORDER BY 
                        l.log_archivo_id;
                    """)
    archivos = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("log_archivos.html", archivos=archivos, nombre_usuario=g.nombre_usuario)


@app.route('/cambiar_estado_usuario/<int:usuario_id>/<int:estado>')
@validar
def cambiar_estado_usuario(usuario_id, estado):
    if g.nombre_usuario != 'admin':
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('camaras'))

    con = obtener_conexion()
    cursor = con.cursor()
    cursor.execute("UPDATE usuarios SET estado_usuario = %s WHERE usuario_id = %s", (estado, usuario_id))
    con.commit()
    cursor.close()
    con.close()
    return redirect(url_for('gestion_usuarios'))


@app.route('/log_archivo', methods=['POST'])
@validar
def log_archivo():
    data = request.get_json()
    nombre_archivo = data.get('nombre_archivo')
    if not nombre_archivo:
        return jsonify({'status': 'error', 'message': 'Nombre de archivo no proporcionado.'}), 400

    # Suponiendo que el usuario está autenticado y su id_usuario está disponible en el token
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'status': 'error', 'message': 'No autorizado 1.'}), 401

    token = auth_header.split(" ")[1]
    print(token)
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

        id_usuario = decoded_token.get('user_id')
        print(decoded_token.get('user_id'))
        if not id_usuario:
            return jsonify({'status': 'error', 'message': 'No autorizado 2.'}), 401

        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO log_archivos (nombre_archivo, usuario_id) VALUES (%s, %s)",
                       (nombre_archivo, id_usuario))
        con.commit()
        cursor.close()
        con.close()

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error al registrar archivo: {e}")
        return jsonify({'status': 'error', 'message': 'Error al registrar archivo.'}), 500


@app.route("/camaras")
@validar
def camaras():
    camaras = controlador_camaras.obtener_camaras()
    return render_template("camaras.html", camaras=camaras, nombre_usuario=g.nombre_usuario)


@app.route("/reportes")
@validar
def reportes():
    camaras = controlador_camaras.obtener_camaras()
    numrep = controlador_reportes.obtener_num_reportes()
    numreg = controlador_reportes.obtener_num_registros()
    return render_template("reportes.html", camaras=camaras, numcam=len(camaras), numprep=numrep, numreg=numreg,
                           nombre_usuario=g.nombre_usuario)


@app.route('/get_report/<int:camara_id>/<int:tiempo>')
@validar
def get_report(camara_id, tiempo):
    print()
    data = controlador_reportes.generar_reporte(camara_id, tiempo)
    return jsonify(data)


@app.route('/get_report_days/<int:camara_id>/<int:tiempo>')
@validar
def get_report_days(camara_id, tiempo):
    print()
    data = controlador_reportes.generar_reporte_dias(camara_id, tiempo)
    return jsonify(data)


@app.route('/get_report_range/<int:camara_id>')
@validar
def get_report_range(camara_id):
    tiempo_i = request.args.get('start_date')
    tiempo_f = request.args.get('end_date')
    data = controlador_reportes.generar_reporte_rango(camara_id, tiempo_i, tiempo_f)
    return jsonify(data)

@app.route('/get_report_days_range/<int:camara_id>')
@validar
def get_report_days_range(camara_id):
    tiempo_i = request.args.get('start_date')
    tiempo_f = request.args.get('end_date')
    data = controlador_reportes.generar_reporte_dias_rango(camara_id, tiempo_i, tiempo_f)
    return jsonify(data)


@app.route('/upload', methods=['POST'])
@validar
def upload_video():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], file.filename)
        selected_cells = [(9, 12), (10, 12), (11, 12)]
        event_list = []

        process_video(filepath, output_filepath, event_list, selected_cells)

        return jsonify({'filename': file.filename, 'events': event_list})


@app.route('/cancel_process', methods=['POST'])
@validar
def cancel_process():
    data = request.get_json()
    process_id = data.get('process_id')
    if not process_id:
        return jsonify({'status': 'error', 'message': 'No process ID provided'}), 400

    if process_id in active_processes:
        active_processes[process_id] = False
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid process ID'}), 400


@app.route('/status', methods=['GET'])
def check_status():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No filename provided'}), 400

    output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(output_filepath):
        event_list = []
        return jsonify({'status': 'completed', 'events': event_list})

    return jsonify({'status': 'processing'})


@app.route('/save_records', methods=['POST'])
@validar
def save_records():
    data = request.get_json()
    fecha = data.get('fecha')
    camara_id = data.get('camara_id')
    registros = data.get('registros')

    if not fecha or not camara_id or not registros:
        return jsonify({'status': 'error', 'message': 'Datos incompletos.'})

    con = obtener_conexion()
    cursor = con.cursor()

    try:
        cursor.execute("INSERT INTO reportes (fecha, camara_id) VALUES (%s, %s) RETURNING reporte_id",
                       (fecha, camara_id))
        reporte_id = cursor.fetchone()[0]

        for registro in registros:
            hora_inicio = registro['hora_inicio']
            hora_final = registro['hora_final']
            cursor.execute("INSERT INTO registros (hora_inicio, hora_final, reporte_id) VALUES (%s, %s, %s)",
                           (hora_inicio, hora_final, reporte_id))

        con.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        con.rollback()
        print(f"Error al guardar registros: {e}")
        return jsonify({'status': 'error', 'message': 'Error al guardar registros.'})
    finally:
        cursor.close()
        con.close()


@app.route('/save', methods=['POST'])
@validar
def save_video():
    if 'file' not in request.files or 'filename' not in request.form:
        return jsonify({'error': 'Faltan parámetros'}), 400
    file = request.files['file']
    filename = request.form['filename']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(filepath)
    return jsonify({'filename': filename})


@app.route('/static/out_videos/<filename>')
@validar
def send_output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, mimetype='video/mp4')


@app.route('/static/input_videos/<filename>')
@validar
def send_input_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, mimetype='video/mp4')


@app.route("/catalogo")
@validar
def catalogo():
    raw_videos = os.listdir(app.config['UPLOAD_FOLDER'])
    processed_videos = os.listdir(app.config['OUTPUT_FOLDER'])
    return render_template("catalogo.html", raw_videos=raw_videos, processed_videos=processed_videos)


# Iniciar el servidor
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
