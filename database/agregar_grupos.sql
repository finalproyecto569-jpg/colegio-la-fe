USE seguimiento_academico;

CREATE TABLE IF NOT EXISTS grupos (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nombre  VARCHAR(10) NOT NULL UNIQUE,
    grado   TINYINT NOT NULL CHECK (grado BETWEEN 1 AND 11)
) ENGINE=InnoDB;

INSERT IGNORE INTO grupos (nombre, grado)
SELECT grupo, MIN(semestre) FROM cursos WHERE grupo IS NOT NULL GROUP BY grupo;
