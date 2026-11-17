from models.conexion import consultar, ejecutar
from models import grupo as modelo_grupo


def listar(texto="", docente_id=None, grupo=None):
    sql = """SELECT c.*, u.nombre AS docente,
                    (SELECT COUNT(*) FROM matriculas m WHERE m.curso_id = c.id) AS total_estudiantes
             FROM cursos c
             LEFT JOIN usuarios u ON u.id = c.docente_id
             WHERE 1=1"""
    parametros = []
    if texto:
        sql += " AND (c.nombre LIKE %s OR c.codigo LIKE %s)"
        parametros += [f"%{texto}%", f"%{texto}%"]
    if docente_id:
        sql += " AND c.docente_id = %s"
        parametros.append(docente_id)
    if grupo == "SIN GRUPO":
        sql += " AND c.grupo IS NULL"
    elif grupo:
        sql += " AND c.grupo = %s"
        parametros.append(grupo)
    sql += " ORDER BY c.semestre, c.nombre"
    return consultar(sql, parametros)


def obtener(id_curso):
    return consultar(
        """SELECT c.*, u.nombre AS docente FROM cursos c
           LEFT JOIN usuarios u ON u.id = c.docente_id WHERE c.id = %s""",
        (id_curso,), uno=True)


def codigo_existe(codigo, excepto_id=None):
    sql = "SELECT id FROM cursos WHERE codigo = %s"
    parametros = [codigo]
    if excepto_id:
        sql += " AND id <> %s"
        parametros.append(excepto_id)
    return consultar(sql, parametros, uno=True) is not None


def crear(datos):
    modelo_grupo.asegurar(datos["grupo"], datos["semestre"])
    return ejecutar(
        "INSERT INTO cursos (codigo, nombre, semestre, grupo, periodo, docente_id) VALUES (%s,%s,%s,%s,%s,%s)",
        (datos["codigo"], datos["nombre"], datos["semestre"], datos["grupo"] or None, datos["periodo"],
         datos["docente_id"] or None),
    )


def actualizar(id_curso, datos):
    modelo_grupo.asegurar(datos["grupo"], datos["semestre"])
    ejecutar(
        "UPDATE cursos SET codigo=%s, nombre=%s, semestre=%s, grupo=%s, periodo=%s, docente_id=%s WHERE id=%s",
        (datos["codigo"], datos["nombre"], datos["semestre"], datos["grupo"] or None, datos["periodo"],
         datos["docente_id"] or None, id_curso),
    )


def eliminar(id_curso):
    ejecutar("DELETE FROM cursos WHERE id = %s", (id_curso,))


def estudiantes_del_curso(id_curso):
    return consultar(
        """SELECT m.id AS matricula_id, u.id, u.nombre, u.documento, u.correo, u.programa
           FROM matriculas m JOIN usuarios u ON u.id = m.estudiante_id
           WHERE m.curso_id = %s ORDER BY u.nombre""",
        (id_curso,))


def estudiantes_disponibles(id_curso):
    return consultar(
        """SELECT id, nombre, documento FROM usuarios
           WHERE rol = 'estudiante' AND activo = 1
             AND id NOT IN (SELECT estudiante_id FROM matriculas WHERE curso_id = %s)
           ORDER BY nombre""",
        (id_curso,))


def matricular(id_curso, id_estudiante):
    ejecutar("INSERT INTO matriculas (estudiante_id, curso_id) VALUES (%s, %s)", (id_estudiante, id_curso))


def retirar(id_matricula):
    ejecutar("DELETE FROM matriculas WHERE id = %s", (id_matricula,))


def cursos_del_estudiante(id_estudiante):
    return consultar(
        """SELECT c.*, m.id AS matricula_id, u.nombre AS docente
           FROM matriculas m JOIN cursos c ON c.id = m.curso_id
           LEFT JOIN usuarios u ON u.id = c.docente_id
           WHERE m.estudiante_id = %s ORDER BY c.nombre""",
        (id_estudiante,))


def grupos():
    nombres = [g["nombre"] for g in modelo_grupo.listar()]
    for nombre in grupos_con_asignaturas():
        if nombre not in nombres:
            nombres.append(nombre)
    return nombres


def grupos_con_asignaturas():
    filas = consultar("SELECT DISTINCT grupo FROM cursos WHERE grupo IS NOT NULL ORDER BY grupo")
    return [f["grupo"] for f in filas]


def contar_matriculas():
    return consultar("SELECT COUNT(*) AS total FROM matriculas", uno=True)["total"]


def matricular_en_grupo(id_estudiante, grupo):
    antes = contar_matriculas()
    ejecutar(
        """INSERT IGNORE INTO matriculas (estudiante_id, curso_id)
           SELECT %s, id FROM cursos WHERE grupo = %s""",
        (id_estudiante, grupo))
    return contar_matriculas() - antes


def matricular_grupo_en_curso(id_curso, grupo):
    antes = contar_matriculas()
    ejecutar(
        """INSERT IGNORE INTO matriculas (estudiante_id, curso_id)
           SELECT id, %s FROM usuarios
           WHERE rol = 'estudiante' AND activo = 1 AND programa = %s""",
        (id_curso, grupo))
    return contar_matriculas() - antes


def resumen_grupos(docente_id=None):
    sql = """SELECT COALESCE(c.grupo, 'SIN GRUPO') AS grupo,
                    MIN(c.semestre) AS grado,
                    COUNT(*) AS asignaturas
             FROM cursos c WHERE 1=1"""
    parametros = []
    if docente_id:
        sql += " AND c.docente_id = %s"
        parametros.append(docente_id)
    sql += " GROUP BY COALESCE(c.grupo, 'SIN GRUPO') ORDER BY MIN(c.semestre), grupo"
    grupos = consultar(sql, parametros)

    if not docente_id:
        ya_estan = [g["grupo"] for g in grupos]
        for g in modelo_grupo.listar():
            if g["nombre"] not in ya_estan:
                grupos.append({"grupo": g["nombre"], "grado": g["grado"], "asignaturas": 0})
        grupos.sort(key=lambda g: (g["grupo"] == "SIN GRUPO", g["grado"] or 99, g["grupo"]))

    for g in grupos:
        g["estudiantes"] = len(estudiantes_del_grupo(g["grupo"]))
        docentes = consultar(
            """SELECT DISTINCT u.nombre FROM cursos c JOIN usuarios u ON u.id = c.docente_id
               WHERE COALESCE(c.grupo, 'SIN GRUPO') = %s ORDER BY u.nombre""", (g["grupo"],))
        g["docentes"] = [d["nombre"] for d in docentes]
    return grupos


def estudiantes_del_grupo(grupo):
    return consultar(
        """SELECT id, nombre, documento FROM usuarios
           WHERE rol = 'estudiante' AND activo = 1 AND programa = %s ORDER BY nombre""",
        (grupo,))
