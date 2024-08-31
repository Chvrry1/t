CREATE TABLE usuarios (usuario_id SERIAL NOT NULL, nombre varchar(20) NOT NULL, clave varchar(50) NOT NULL, PRIMARY KEY (usuario_id));
CREATE TABLE registros (registro_id SERIAL NOT NULL, hora_inicio timestamp NOT NULL, hora_final timestamp NOT NULL, reporte_id int4 NOT NULL, PRIMARY KEY (registro_id));
CREATE TABLE camaras (camara_id SERIAL NOT NULL, nombre varchar(255) NOT NULL, estado varchar(11) NOT NULL, PRIMARY KEY (camara_id));
CREATE TABLE reportes (reporte_id SERIAL NOT NULL, fecha date NOT NULL, camara_id int4 NOT NULL, PRIMARY KEY (reporte_id));
ALTER TABLE reportes ADD CONSTRAINT FKreportes811088 FOREIGN KEY (camara_id) REFERENCES camaras (camara_id);
ALTER TABLE registros ADD CONSTRAINT FKregistros32696 FOREIGN KEY (reporte_id) REFERENCES reportes (reporte_id);
ALTER TABLE usuarios ADD CONSTRAINT unique_nombre UNIQUE (nombre);
INSERT INTO camaras (nombre) VALUES
('Avenida Libertador - Calle 25 de Mayo'),
('Calle San Martín - Avenida Belgrano');


-- Tabla log_sesiones
CREATE TABLE log_sesiones (
    log_sesion_id SERIAL PRIMARY KEY, 
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    usuario_id INTEGER,  
    CONSTRAINT fk_usuario_sesiones
        FOREIGN KEY(usuario_id) 
        REFERENCES usuarios(usuario_id) 
);

-- Tabla log_archivos
CREATE TABLE log_archivos (
    log_archivo_id SERIAL PRIMARY KEY, 
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    nombre_archivo VARCHAR(255) NOT NULL,
    usuario_id INTEGER,  
    CONSTRAINT fk_usuario_archivos
        FOREIGN KEY(usuario_id) 
        REFERENCES usuarios(usuario_id) 
);