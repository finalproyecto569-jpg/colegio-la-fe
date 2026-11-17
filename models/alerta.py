from flask import current_app
from models.conexion import consultar, ejecutar
from models.reporte import resumen_matriculas

TIPOS = ["rendimiento", "inasistencia", "riesgo", "otro"]
NIVELES = ["baja", "media", "alta"]
ESTADOS = ["abierta", "en_seguimiento", "cerrada"]


def listar(estado="", nivel="", tipo="", texto="", docente_id=None, estudiante_id=None, grupo=""):
    sql = """SELECT a.*, e.nombre AS estudiante, e.documento, e.programa AS grupo, c.nombre AS curso, c.codigo,
                    u.nombre AS creador
             FROM alertas a
             JOIN usuarios e ON e.id = a.estudiante_id
             LEFT JOIN cursos c ON c.id = a.curso_id
             LEFT JOIN usuarios u ON u.id = a.creado_por
             WHERE 1=1"""
    parametros = []
    if estado:
        sql += " AND a.estado = %s"
        parametros.append(estado)
    if nivel:
        sql += " AND a.nivel = %s"
        parametros.append(nivel)
    if tipo:
        sql += " AND a.tipo = %s"
        parametros.append(tipo)
    if texto:
        sql += " AND (e.nombre LIKE %s OR e.documento LIKE %s OR a.descripcion LIKE %s)"
        parametros += [f"%{texto}%"] * 3
    if docente_id:
        sql += " AND (c.docente_id = %s OR a.creado_por = %s)"
        parametros += [docente_id, docente_id]
    if estudiante_id:
        sql += " AND a.estudiante_id = %s"
        parametros.append(estudiante_id)
    if grupo:
        sql += " AND e.programa = %s"
        parametros.append(grupo)
    sql += """ ORDER BY CASE a.estado WHEN 'abierta' THEN 1 WHEN 'en_seguimiento' THEN 2 ELSE 3 END,
                        CASE a.nivel WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END,
                        a.fecha_creacion DESC"""
    return consultar(sql, parametros)


def obtener(id_alerta):
    return consultar(
        """SELECT a.*, e.nombre AS estudiante, e.programa AS grupo, c.nombre AS curso, c.docente_id
           FROM alertas a JOIN usuarios e ON e.id = a.estudiante_id
           LEFT JOIN cursos c ON c.id = a.curso_id WHERE a.id = %s""",
        (id_alerta,), uno=True)


def crear(datos, creado_por, origen="manual"):
    return ejecutar(
        """INSERT INTO alertas (estudiante_id, curso_id, tipo, nivel, descripcion, estado, seguimiento, origen, creado_por)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (datos["estudiante_id"], datos.get("curso_id") or None, datos["tipo"], datos["nivel"],
         datos["descripcion"], datos.get("estado", "abierta"), datos.get("seguimiento") or None,
         origen, creado_por))


def actualizar(id_alerta, datos):
    ejecutar(
        """UPDATE alertas SET estudiante_id=%s, curso_id=%s, tipo=%s, nivel=%s, descripcion=%s, estado=%s,
                  seguimiento=%s, fecha_actualizacion = NOW()
           WHERE id = %s""",
        (datos["estudiante_id"], datos.get("curso_id") or None, datos["tipo"], datos["nivel"],
         datos["descripcion"], datos["estado"], datos.get("seguimiento") or None, id_alerta))


def eliminar(id_alerta):
    ejecutar("DELETE FROM alertas WHERE id = %s", (id_alerta,))


def contar_por(campo, docente_id=None, estudiante_id=None, grupo=""):
    if campo not in ("estado", "nivel", "tipo"):
        return {}
    sql = f"""SELECT a.{campo} AS clave, COUNT(*) AS total FROM alertas a
              JOIN usuarios e ON e.id = a.estudiante_id
              LEFT JOIN cursos c ON c.id = a.curso_id WHERE 1=1"""
    parametros = []
    if docente_id:
        sql += " AND (c.docente_id = %s OR a.creado_por = %s)"
        parametros += [docente_id, docente_id]
    if estudiante_id:
        sql += " AND a.estudiante_id = %s"
        parametros.append(estudiante_id)
    if grupo:
        sql += " AND e.programa = %s"
        parametros.append(grupo)
    if campo != "estado":
        sql += " AND a.estado <> 'cerrada'"
    sql += f" GROUP BY a.{campo}"
    return {f["clave"]: f["total"] for f in consultar(sql, parametros)}


def _ya_existe(estudiante_id, curso_id, tipo):
    return consultar(
        """SELECT id FROM alertas WHERE estudiante_id = %s AND curso_id <=> %s AND tipo = %s
           AND estado <> 'cerrada'""",
        (estudiante_id, curso_id, tipo), uno=True) is not None


def generar_automaticas(creado_por=None, curso_id=None):
    nota_minima = current_app.config["NOTA_MINIMA"]
    max_fallas = current_app.config["MAX_INASISTENCIA"]
    creadas = 0

    for r in resumen_matriculas(curso_id=curso_id):
        tipo = None
        if r["bajo_rendimiento"] and r["muchas_fallas"]:
            tipo, nivel = "riesgo", "alta"
            texto = (f"Riesgo académico en {r['curso']}: promedio {r['promedio']} "
                     f"y {r['pct_inasistencia']}% de inasistencia.")
        elif r["bajo_rendimiento"]:
            tipo = "rendimiento"
            nivel = "alta" if r["promedio"] < 2.0 else "media"
            texto = f"Bajo rendimiento en {r['curso']}: promedio {r['promedio']} (mínimo {nota_minima})."
        elif r["muchas_fallas"]:
            tipo = "inasistencia"
            nivel = "alta" if r["pct_inasistencia"] > max_fallas * 1.5 else "media"
            texto = (f"Inasistencia en {r['curso']}: {r['fallas']} fallas de {r['clases']} clases "
                     f"({r['pct_inasistencia']}%).")

        if tipo and not _ya_existe(r["estudiante_id"], r["curso_id"], tipo):
            crear({"estudiante_id": r["estudiante_id"], "curso_id": r["curso_id"], "tipo": tipo,
                   "nivel": nivel, "descripcion": texto}, creado_por, origen="automatica")
            creadas += 1
    return creadas
