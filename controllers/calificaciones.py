from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import curso, calificacion, alerta
from utils.seguridad import roles_permitidos, puede_gestionar_curso, docente_filtro

calificaciones_bp = Blueprint("calificaciones", __name__, url_prefix="/calificaciones")


@calificaciones_bp.route("/")
@roles_permitidos("administrador", "coordinador", "docente")
def seleccionar():
    grupo = request.args.get("grupo", "").strip()
    if not grupo:
        return render_template("elegir_grupo.html", grupos=curso.resumen_grupos(docente_filtro()),
                               titulo="Calificaciones", inicio="calificaciones.seleccionar",
                               texto="Elige un grupo para ver sus asignaturas.")
    return render_template("elegir_curso.html", cursos=curso.listar(docente_id=docente_filtro(), grupo=grupo),
                           titulo="Calificaciones", destino="calificaciones.planilla", grupo=grupo,
                           inicio="calificaciones.seleccionar",
                           texto="Elige la asignatura para registrar o editar las notas de cada corte.")


@calificaciones_bp.route("/<int:id_curso>", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def planilla(id_curso):
    c = curso.obtener(id_curso)
    if c is None:
        abort(404)
    if not puede_gestionar_curso(c):
        abort(403)

    estudiantes = curso.estudiantes_del_curso(id_curso)

    if request.method == "POST":
        errores = []
        cambios = 0
        for est in estudiantes:
            for corte in (1, 2, 3):
                campo = f"nota_{est['matricula_id']}_{corte}"
                valor = request.form.get(campo, "").strip().replace(",", ".")
                if valor == "":
                    calificacion.eliminar(est["matricula_id"], corte)
                    continue
                try:
                    nota = float(valor)
                except ValueError:
                    errores.append(f"{est['nombre']}: la nota del corte {corte} no es un número.")
                    continue
                if not 0 <= nota <= 5:
                    errores.append(f"{est['nombre']}: la nota del corte {corte} debe estar entre 0 y 5.")
                    continue
                calificacion.guardar(est["matricula_id"], corte, round(nota, 1))
                cambios += 1

        for e in errores:
            flash(e, "error")
        nuevas = alerta.generar_automaticas(creado_por=session["usuario_id"], curso_id=id_curso)
        flash(f"Notas guardadas ({cambios} registradas).", "exito")
        if nuevas:
            flash(f"Se generaron {nuevas} alerta(s) nueva(s) por bajo rendimiento.", "aviso")
        return redirect(url_for("calificaciones.planilla", id_curso=id_curso))

    return render_template("calificaciones/planilla.html", curso=c, estudiantes=estudiantes,
                           notas=calificacion.notas_del_curso(id_curso))
