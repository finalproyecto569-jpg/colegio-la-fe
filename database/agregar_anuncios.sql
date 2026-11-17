USE seguimiento_academico;

CREATE TABLE IF NOT EXISTS anuncios (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    titulo             VARCHAR(150) NOT NULL,
    descripcion        TEXT NOT NULL,
    fecha_evento       DATE NULL,
    imagen             VARCHAR(255) NULL,
    autor_id           INT NULL,
    fecha_publicacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_anuncios_autor FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT IGNORE INTO anuncios (id, titulo, descripcion, fecha_evento, imagen, autor_id, fecha_publicacion) VALUES
(1, 'Feria de la ciencia 2026', 'Los estudiantes de 9° y 10° presentarán sus proyectos de ciencias en el patio central. Están invitadas todas las familias.
Hora: 8:00 a.m. a 12:00 m.', '2026-11-20', 'uploads/anuncios/ejemplo_feria.png', 2, '2026-11-05 09:30:00'),
(2, 'Entrega de boletines del tercer periodo', 'Los acudientes deben asistir a la reunión con el director de grupo para recibir el boletín y conocer el seguimiento académico de su hijo(a).', '2026-11-27', NULL, 2, '2026-11-08 14:00:00'),
(3, 'Jornada de refuerzo académico', 'Los estudiantes con alertas de rendimiento o inasistencia podrán asistir a tutorías los martes y jueves en la tarde. Inscríbete con tu docente.', NULL, NULL, 2, '2026-11-10 11:15:00');
