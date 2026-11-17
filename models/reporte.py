from flask import current_app
from models.conexion import consultar
from models.calificacion import calcular_promedio


def resumen_matriculas(curso_id=None, docente_id=None, estudiante_id=None, programa="", texto=""):
    sql = """
        SELECT m.id AS matricula_id,
               e.id AS estudiante_id, e.nombre AS estudiante, e.documento, e.programa,
               c.id AS curso_id, c.codigo, c.nombre AS curso, d.nombre AS docente,
               (SELECT nota FROM calificaciones n WHERE n.matricula_id = m.id AND n.corte = 1) AS corte1,
               (SELECT nota FROM calificaciones n WHERE n.matricula_id = m.id AND n.corte = 2) AS corte2,
               (SELECT nota FROM calificaciones n WHERE n.matricula_id = m.id AND n.corte = 3) AS corte3,
               (SELECT COUNT(*) FROM asistencias a WHERE a.matricula_id = m.id) AS clases,
               (SELECT COUNT(*) FROM asistencias a WHERE a.matricula_id = m.id AND a.estado = 'ausente') AS fallas
        FROM matriculas m
        JOIN usuarios e ON e.id = m.estudiante_id
        JOIN cursos c   ON c.id = m.curso_id
        LEFT JOIN usuarios d ON d.id = c.docente_id
        WHERE 1=1
    """
    parametros = []
    if curso_id:
        sql += " AND c.id = %s"
        parametros.append(curso_id)
    if docente_id:
        sql += " AND c.docente_id = %s"
        parametros.append(docente_id)
    if estudiante_id:
        sql += " AND e.id = %s"
        parametros.append(estudiante_id)
    if programa:
        sql += " AND e.programa = %s"
        parametros.append(programa)
    if texto:
        sql += " AND (e.nombre LIKE %s OR e.documento LIKE %s)"
        parametros += [f"%{texto}%", f"%{texto}%"]
    sql += " ORDER BY c.nombre, e.nombre"

    nota_minima = current_app.config["NOTA_MINIMA"]
    max_fallas = current_app.config["MAX_INASISTENCIA"]

    resultado = []
    for fila in consultar(sql, parametros):
        r = dict(fila)
        r["promedio"] = calcular_promedio({1: r["corte1"], 2: r["corte2"], 3: r["corte3"]})
        r["pct_inasistencia"] = round(r["fallas"] * 100 / r["clases"], 1) if r["clases"] else 0
        r["pct_asistencia"] = round(100 - r["pct_inasistencia"], 1) if r["clases"] else None

        bajo_rendimiento = r["promedio"] is not None and r["promedio"] < nota_minima
        muchas_fallas = r["pct_inasistencia"] > max_fallas
        r["bajo_rendimiento"] = bajo_rendimiento
        r["muchas_fallas"] = muchas_fallas

        if r["promedio"] is None and not r["clases"]:
            r["riesgo"] = "sin datos"
        elif (bajo_rendimiento and muchas_fallas) or (r["promedio"] is not None and r["promedio"] < 2.0):
            r["riesgo"] = "alto"
        elif bajo_rendimiento or muchas_fallas:
            r["riesgo"] = "medio"
        else:
            r["riesgo"] = "bajo"
        resultado.append(r)
    return resultado


def promedio_por_curso(docente_id=None):
    filas = resumen_matriculas(docente_id=docente_id)
    cursos = {}
    for r in filas:
        c = cursos.setdefault(r["curso_id"], {"curso": r["codigo"], "nombre": r["curso"],
                                              "notas": [], "asis": []})
        if r["promedio"] is not None:
            c["notas"].append(r["promedio"])
        if r["pct_asistencia"] is not None:
            c["asis"].append(r["pct_asistencia"])
    salida = []
    for c in cursos.values():
        salida.append({
            "curso": c["curso"],
            "nombre": c["nombre"],
            "promedio": round(sum(c["notas"]) / len(c["notas"]), 2) if c["notas"] else 0,
            "asistencia": round(sum(c["asis"]) / len(c["asis"]), 1) if c["asis"] else 0,
        })
    return salida


def promedio_por_grupo(docente_id=None):
    filas = resumen_matriculas(docente_id=docente_id)
    grupos = {}
    for r in filas:
        nombre = r["programa"] or "Sin grupo"
        g = grupos.setdefault(nombre, {"notas": [], "asis": []})
        if r["promedio"] is not None:
            g["notas"].append(r["promedio"])
        if r["pct_asistencia"] is not None:
            g["asis"].append(r["pct_asistencia"])

    def numero_de_grado(nombre):
        digitos = "".join(ch for ch in nombre if ch.isdigit())
        return int(digitos) if digitos else 99

    salida = []
    for nombre in sorted(grupos, key=lambda n: (numero_de_grado(n), n)):
        g = grupos[nombre]
        salida.append({
            "curso": nombre,
            "nombre": "Grupo " + nombre,
            "promedio": round(sum(g["notas"]) / len(g["notas"]), 2) if g["notas"] else 0,
            "asistencia": round(sum(g["asis"]) / len(g["asis"]), 1) if g["asis"] else 0,
        })
    return salida


def conteo_riesgo(filas):
    conteo = {"alto": 0, "medio": 0, "bajo": 0, "sin datos": 0}
    for r in filas:
        conteo[r["riesgo"]] += 1
    return conteo
