from datetime import date, timedelta
from models.conexion import consultar
from models import curso, reporte, alerta


def datos_docente(id_docente):
    filas = reporte.resumen_matriculas(docente_id=id_docente)
    materias = []
    for c in curso.listar(docente_id=id_docente):
        mis = [r for r in filas if r["curso_id"] == c["id"]]
        notas = [r["promedio"] for r in mis if r["promedio"] is not None]
        ultima = consultar(
            """SELECT MAX(a.fecha) AS ultima FROM asistencias a JOIN matriculas m ON m.id = a.matricula_id
               WHERE m.curso_id = %s""", (c["id"],), uno=True)["ultima"]
        sin_nota = {corte: sum(1 for r in mis if r[f"corte{corte}"] is None) for corte in (1, 2, 3)}
        materias.append({
            **c,
            "promedio": round(sum(notas) / len(notas), 2) if notas else "-",
            "en_riesgo": sum(1 for r in mis if r["riesgo"] in ("alto", "medio")),
            "ultima_asistencia": ultima,
            "sin_nota": sin_nota,
            "alertas": len([a for a in alerta.listar(estado="abierta", docente_id=id_docente) if a["curso_id"] == c["id"]]),
        })

    pendientes = []
    hoy = date.today()
    for m in materias:
        for corte, faltan in m["sin_nota"].items():
            if faltan:
                pendientes.append({"texto": f"{m['nombre']}: faltan {faltan} nota(s) del corte {corte}",
                                   "boton": "Poner notas", "destino": ("calificaciones.planilla", m["id"]), "tipo": "notas"})
                break
    total_alertas = sum(m["alertas"] for m in materias)
    if total_alertas:
        pendientes.append({"texto": f"Tienes {total_alertas} alerta(s) abiertas por atender",
                           "boton": "Ver alertas", "destino": ("alertas.lista", None), "tipo": "alertas"})

    estudiantes = len({r["estudiante_id"] for r in filas})
    return {"materias": materias, "pendientes": pendientes,
            "indicadores": {"materias": len(materias), "estudiantes": estudiantes, "alertas": total_alertas}}