from flask import Blueprint, render_template, redirect, url_for, session, jsonify
from models import usuario, curso, alerta, reporte, asistencia, anuncio
from utils.seguridad import login_requerido, roles_permitidos, docente_filtro

principal_bp = Blueprint("principal", __name__)


@principal_bp.route("/")
@login_requerido
def inicio():
    if session["rol"] == "estudiante":
        return redirect(url_for("principal.mi_panel"))
    return redirect(url_for("principal.dashboard"))


@principal_bp.route("/dashboard")
@roles_permitidos("administrador", "coordinador", "docente")
def dashboard():
    if session["rol"] == "docente":
        from models.panel_docente import datos_docente
        return render_template("docente/panel.html", d=datos_docente(session["usuario_id"]),
                               anuncios=anuncio.listar())

    id_docente = docente_filtro()
    filas = reporte.resumen_matriculas(docente_id=id_docente)
    riesgo = reporte.conteo_riesgo(filas)

    estudiantes_unicos = {r["estudiante_id"] for r in filas}
    promedios = [r["promedio"] for r in filas if r["promedio"] is not None]
    asistencias = [r["pct_asistencia"] for r in filas if r["pct_asistencia"] is not None]
    alertas_estado = alerta.contar_por("estado", docente_id=id_docente)

    indicadores = {
        "estudiantes": len(estudiantes_unicos),
        "cursos": len(curso.listar(docente_id=id_docente)),
        "promedio": round(sum(promedios) / len(promedios), 2) if promedios else 0,
        "asistencia": round(sum(asistencias) / len(asistencias), 1) if asistencias else 0,
        "alertas_abiertas": alertas_estado.get("abierta", 0) + alertas_estado.get("en_seguimiento", 0),
        "en_riesgo": riesgo["alto"] + riesgo["medio"],
    }

    return render_template("dashboard.html", indicadores=indicadores, anuncios=anuncio.listar())


@principal_bp.route("/api/dashboard")
@roles_permitidos("administrador", "coordinador")
def api_dashboard():
    id_docente = docente_filtro()
    filas = reporte.resumen_matriculas(docente_id=id_docente)
    return jsonify({
        "cursos": reporte.promedio_por_curso(docente_id=id_docente),
        "grupos": reporte.promedio_por_grupo(docente_id=id_docente),
        "riesgo": reporte.conteo_riesgo(filas),
        "alertas_nivel": alerta.contar_por("nivel", docente_id=id_docente),
        "alertas_tipo": alerta.contar_por("tipo", docente_id=id_docente),
        "usuarios": usuario.contar_por_rol() if not id_docente else None,
    })


@principal_bp.route("/mi-panel")
@roles_permitidos("estudiante")
def mi_panel():
    id_est = session["usuario_id"]
    filas = reporte.resumen_matriculas(estudiante_id=id_est)
    promedios = [r["promedio"] for r in filas if r["promedio"] is not None]

    historial = {r["matricula_id"]: asistencia.asistencia_de_matricula(r["matricula_id"]) for r in filas}

    return render_template(
        "mi_panel.html",
        estudiante=usuario.obtener(id_est),
        filas=filas,
        historial=historial,
        promedio_general=round(sum(promedios) / len(promedios), 2) if promedios else None,
        alertas=alerta.listar(estudiante_id=id_est),
        anuncios=anuncio.listar(),


    )


@principal_bp.route("/mis-alertas")
@roles_permitidos("estudiante")
def mis_alertas():
    alertas = alerta.listar(estudiante_id=session["usuario_id"])
    abiertas = [a for a in alertas if a["estado"] != "cerrada"]
    return render_template("mis_alertas.html", alertas=alertas, abiertas=len(abiertas))