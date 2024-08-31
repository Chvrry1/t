CREATE TABLE usuarios (usuario_id SERIAL NOT NULL, nombre varchar(20) NOT NULL, clave varchar(50) NOT NULL, PRIMARY KEY (usuario_id));
CREATE TABLE registros (registro_id SERIAL NOT NULL, hora_inicio timestamp NOT NULL, hora_final timestamp NOT NULL, reporte_id int4 NOT NULL, PRIMARY KEY (registro_id));
CREATE TABLE camaras (camara_id SERIAL NOT NULL, nombre varchar(255) NOT NULL, estado varchar(11) NOT NULL, PRIMARY KEY (camara_id));
CREATE TABLE reportes (reporte_id SERIAL NOT NULL, fecha date NOT NULL, camara_id int4 NOT NULL, PRIMARY KEY (reporte_id));
ALTER TABLE reportes ADD CONSTRAINT FKreportes811088 FOREIGN KEY (camara_id) REFERENCES camaras (camara_id);
ALTER TABLE registros ADD CONSTRAINT FKregistros32696 FOREIGN KEY (reporte_id) REFERENCES reportes (reporte_id);
