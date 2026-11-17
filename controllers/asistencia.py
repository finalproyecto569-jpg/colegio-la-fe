from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import curso, asistencia, alerta
from utils.seguridad import roles_permitidos, puede_gestionar_curso, docente_filtro
from utils.correo import avisar_inasistencia

asistencia_bp = Blueprint("asistencia", __name__, url_prefix="/asistencia")


def fecha_valida(texto):
    try:
        f = datetime.strptime(texto, "%Y-%m-%d").date()
        return f <= date.today()
    except ValueError:
        return False


def curso_permitido(id_curso):
    c = curso.obtener(id_curso)
    if c is None:
        abort(404)
    if not puede_gestionar_curso(c):
        abort(403)
    return c


@asistencia_bp.route("/")
@roles_permitidos("administrador", "coordinador", "docente")
def seleccionar():
    grupo = request.args.get("grupo", "").strip()
    if not grupo:
        return render_template("elegir_grupo.html", grupos=curso.resumen_grupos(docente_filtro()),
                               titulo="Asistencia", inicio="asistencia.seleccionar",
                               texto="Elige un grupo para ver sus asignaturas.")
    return render_template("elegir_curso.html", cursos=curso.listar(docente_id=docente_filtro(), grupo=grupo),
                           titulo="Asistencia", destino="asistencia.planilla", grupo=grupo,
                           inicio="asistencia.seleccionar",
                           texto="Elige la asignatura para tomar asistencia o revisar el historial.")


@asistencia_bp.route("/<int:id_curso>", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def planilla(id_curso):
    c = curso_permitido(id_curso)
    fecha = request.values.get("fecha", date.today().isoformat())
    if not fecha_valida(fecha):
        flash("La fecha no es válida (no puede ser futura).", "error")
        fecha = date.today().isoformat()

    estudiantes = curso.estudiantes_del_curso(id_curso)

    if request.method == "POST":
        guardados = 0
        correos = 0
        antes = asistencia.asistencia_del_dia(id_curso, fecha)
        for est in estudiantes:
            estado = request.form.get(f"estado_{est['matricula_id']}")
            if estado in asistencia.ESTADOS:
                asistencia.guardar(est["matricula_id"], fecha, estado)
                guardados += 1
                if estado == "ausente" and antes.get(est["matricula_id"]) != "ausente":
                    if avisar_inasistencia(est, c, fecha):
                        correos += 1
        if correos:
            flash(f"Se envió el aviso de inasistencia por correo a {correos} estudiante(s).", "aviso")
        if guardados == 0:
            flash("No marcaste la asistencia de ningún estudiante.", "error")
        else:
            flash(f"Asistencia del {fecha} guardada ({guardados} estudiantes).", "exito")
            nuevas = alerta.generar_automaticas(creado_por=session["usuario_id"], curso_id=id_curso)
            if nuevas:
                flash(f"Se generaron {nuevas} alerta(s) nueva(s) por inasistencia.", "aviso")
        return redirect(url_for("asistencia.planilla", id_curso=id_curso, fecha=fecha))

    return render_template("asistencia/planilla.html", curso=c, estudiantes=estudiantes, fecha=fecha,
                           marcados=asistencia.asistencia_del_dia(id_curso, fecha),
                           historial=asistencia.fechas_del_curso(id_curso), hoy=date.today().isoformat())


@asistencia_bp.route("/<int:id_curso>/eliminar", methods=["POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def eliminar(id_curso):
    curso_permitido(id_curso)
    fecha = request.form.get("fecha", "")
    asistencia.eliminar_fecha(id_curso, fecha)
    flash(f"Se eliminó la asistencia del {fecha}.", "exito")
    return redirect(url_for("asistencia.planilla", id_curso=id_curso))
