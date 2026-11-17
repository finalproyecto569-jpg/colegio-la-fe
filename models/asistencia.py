from models.conexion import consultar, ejecutar

ESTADOS = ["presente", "ausente", "justificada"]


def asistencia_del_dia(id_curso, fecha):
    filas = consultar(
        """SELECT a.matricula_id, a.estado FROM asistencias a
           JOIN matriculas m ON m.id = a.matricula_id
           WHERE m.curso_id = %s AND a.fecha = %s""",
        (id_curso, fecha))
    return {f["matricula_id"]: f["estado"] for f in filas}


def guardar(id_matricula, fecha, estado):
    ejecutar(
        """INSERT INTO asistencias (matricula_id, fecha, estado) VALUES (%s,%s,%s)
           ON DUPLICATE KEY UPDATE estado = VALUES(estado)""",
        (id_matricula, fecha, estado))


def fechas_del_curso(id_curso):
    return consultar(
        """SELECT a.fecha,
                  COUNT(CASE WHEN a.estado = 'presente' THEN 1 END) AS presentes,
                  COUNT(CASE WHEN a.estado = 'ausente' THEN 1 END) AS ausentes,
                  COUNT(CASE WHEN a.estado = 'justificada' THEN 1 END) AS justificadas
           FROM asistencias a JOIN matriculas m ON m.id = a.matricula_id
           WHERE m.curso_id = %s
           GROUP BY a.fecha ORDER BY a.fecha DESC""",
        (id_curso,))


def eliminar_fecha(id_curso, fecha):
    ejecutar(
        """DELETE FROM asistencias
           WHERE fecha = %s AND matricula_id IN (SELECT id FROM matriculas WHERE curso_id = %s)""",
        (fecha, id_curso))


def asistencia_de_matricula(id_matricula):
    return consultar("SELECT fecha, estado FROM asistencias WHERE matricula_id = %s ORDER BY fecha DESC",
                     (id_matricula,))
