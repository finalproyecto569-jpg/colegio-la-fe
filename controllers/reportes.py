from datetime import date
from flask import Blueprint, render_template, request
from models import curso, usuario, reporte
from utils.seguridad import roles_permitidos, docente_filtro

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def obtener_filtros():
    return {
        "curso_id": request.args.get("curso", type=int),
        "programa": request.args.get("programa", ""),
        "riesgo": request.args.get("riesgo", ""),
        "texto": request.args.get("q", "").strip(),
    }


def filas_filtradas(f):
    filas = reporte.resumen_matriculas(curso_id=f["curso_id"], docente_id=docente_filtro(),
                                       programa=f["programa"], texto=f["texto"])
    if f["riesgo"]:
        filas = [r for r in filas if r["riesgo"] == f["riesgo"]]
    return filas


def resumen_de(filas):
    promedios = [r["promedio"] for r in filas if r["promedio"] is not None]
    return {
        "total": len(filas),
        "promedio": round(sum(promedios) / len(promedios), 2) if promedios else "-",
        "aprobando": sum(1 for r in filas if r["promedio"] is not None and not r["bajo_rendimiento"]),
        "riesgo": reporte.conteo_riesgo(filas),
    }


@reportes_bp.route("/")
@roles_permitidos("administrador", "coordinador", "docente")
def index():
    if not request.args:
        tarjetas = []
        for g in curso.resumen_grupos(docente_filtro()):
            if g["grupo"] == "SIN GRUPO":
                continue
            filas = reporte.resumen_matriculas(docente_id=docente_filtro(), programa=g["grupo"])
            tarjetas.append({"grupo": g["grupo"], "grado": g["grado"], **resumen_de(filas)})
        return render_template("reportes/grupos.html", tarjetas=tarjetas)

    f = obtener_filtros()
    filas = filas_filtradas(f)
    resumen = resumen_de(filas)
    return render_template("reportes/index.html", filas=filas, filtros=f, resumen=resumen,
                           cursos=curso.listar(docente_id=docente_filtro()), programas=usuario.programas(),
                           hoy=date.today().isoformat())
