import pymysql
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import curso, usuario, reporte
from models import grupo as modelo_grupo
from utils.seguridad import roles_permitidos, puede_gestionar_curso, docente_filtro

cursos_bp = Blueprint("cursos", __name__, url_prefix="/cursos")


def leer_formulario():
    return {
        "codigo": request.form.get("codigo", "").strip().upper(),
        "nombre": request.form.get("nombre", "").strip(),
        "semestre": request.form.get("semestre", "").strip(),
        "grupo": request.form.get("grupo", "").strip().upper(),
        "periodo": request.form.get("periodo", "").strip(),
        "docente_id": request.form.get("docente_id", ""),
    }


def validar(datos, id_curso=None):
    errores = []
    if len(datos["codigo"]) < 3:
        errores.append("El código debe tener al menos 3 caracteres.")
    elif curso.codigo_existe(datos["codigo"], id_curso):
        errores.append("Ya existe un curso con ese código.")
    if len(datos["nombre"]) < 3:
        errores.append("El nombre del curso es obligatorio.")
    if not datos["semestre"].isdigit() or not 1 <= int(datos["semestre"]) <= 11:
        errores.append("El grado debe ser un número entre 1 y 11.")
    if not datos["periodo"]:
        errores.append("El año lectivo es obligatorio (ej: 2026).")
    return errores


@cursos_bp.route("/")
@roles_permitidos("administrador", "coordinador", "docente")
def lista():
    grupo = request.args.get("grupo", "").strip()
    if not grupo:
        return render_template("cursos/lista.html", grupos=curso.resumen_grupos(docente_filtro()))

    asignaturas = curso.listar(docente_id=docente_filtro(), grupo=grupo)

    promedios = {}
    for fila in reporte.resumen_matriculas(docente_id=docente_filtro(), programa=grupo):
        if fila["promedio"] is not None:
            promedios.setdefault(fila["estudiante_id"], []).append(fila["promedio"])
    estudiantes = []
    for e in curso.estudiantes_del_grupo(grupo):
        notas = promedios.get(e["id"], [])
        estudiantes.append({**e, "promedio": round(sum(notas) / len(notas), 2) if notas else None})

    return render_template("cursos/grupo.html", grupo=grupo, asignaturas=asignaturas, estudiantes=estudiantes)


@cursos_bp.route("/nuevo", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador")
def nuevo():
    grupo = request.args.get("grupo", "")
    grado = "".join(ch for ch in grupo if ch.isdigit())
    datos = {"periodo": "2026", "grupo": grupo, "semestre": grado}
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos)
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            nuevo_id = curso.crear(datos)
            flash("Asignatura creada.", "exito")
            if datos["grupo"]:
                n = curso.matricular_grupo_en_curso(nuevo_id, datos["grupo"])
                flash(f"Se matricularon automáticamente {n} estudiante(s) del grupo {datos['grupo']}.", "exito")
            return redirect(url_for("cursos.detalle", id=nuevo_id))
    return render_template("cursos/form.html", datos=datos, docentes=usuario.listar_por_rol("docente"),
                           grupos=curso.grupos(), editando=False)


@cursos_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador")
def editar(id):
    c = curso.obtener(id)
    if c is None:
        abort(404)
    datos = dict(c)
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos, id)
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            curso.actualizar(id, datos)
            flash("Asignatura actualizada.", "exito")
            if datos["grupo"]:
                n = curso.matricular_grupo_en_curso(id, datos["grupo"])
                if n:
                    flash(f"Se matricularon {n} estudiante(s) nuevos del grupo {datos['grupo']}.", "exito")
            return redirect(url_for("cursos.lista", grupo=datos["grupo"] or "SIN GRUPO"))
    datos["id"] = id
    return render_template("cursos/form.html", datos=datos, docentes=usuario.listar_por_rol("docente"),
                           grupos=curso.grupos(), editando=True)


@cursos_bp.route("/<int:id>/eliminar", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def eliminar(id):
    c = curso.obtener(id)
    if c is None:
        flash("La asignatura no existe.", "error")
        return redirect(url_for("cursos.lista"))
    curso.eliminar(id)
    flash("Asignatura eliminada junto con sus matrículas, notas y asistencia.", "exito")
    return redirect(url_for("cursos.lista", grupo=c["grupo"] or "SIN GRUPO"))


@cursos_bp.route("/<int:id>")
@roles_permitidos("administrador", "coordinador", "docente")
def detalle(id):
    c = curso.obtener(id)
    if c is None:
        abort(404)
    if not puede_gestionar_curso(c):
        abort(403)
    return render_template("cursos/detalle.html", curso=c,
                           estudiantes=curso.estudiantes_del_curso(id),
                           disponibles=curso.estudiantes_disponibles(id))


@cursos_bp.route("/<int:id>/matricular", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def matricular(id):
    ids = request.form.getlist("estudiantes")
    if not ids:
        flash("Selecciona al menos un estudiante.", "error")
        return redirect(url_for("cursos.detalle", id=id))
    agregados = 0
    for id_est in ids:
        try:
            curso.matricular(id, int(id_est))
            agregados += 1
        except (pymysql.err.IntegrityError, ValueError):
            pass
    flash(f"{agregados} estudiante(s) matriculado(s).", "exito")
    return redirect(url_for("cursos.detalle", id=id))


@cursos_bp.route("/<int:id>/retirar/<int:id_matricula>", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def retirar(id, id_matricula):
    curso.retirar(id_matricula)
    flash("Estudiante retirado del curso.", "exito")
    return redirect(url_for("cursos.detalle", id=id))


LETRAS = ["A", "B", "C", "D", "E", "F"]

@cursos_bp.route("/grupos/nuevo", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador")
def nuevo_grupo():
    datos = {"grado": "", "letra": "A"}
    if request.method == "POST":
        datos = {
            "grado": request.form.get("grado", "").strip(),
            "letra": request.form.get("letra", "").strip().upper(),
        }
        errores = []
        if not datos["grado"].isdigit() or not 1 <= int(datos["grado"]) <= 11:
            errores.append("El grado debe ser un número entre 1 y 11.")
        if datos["letra"] not in LETRAS:
            errores.append("Escoge la letra del grupo.")
        datos["nombre"] = f"{datos['grado']}°{datos['letra']}" if not errores else ""
        if datos["nombre"] and datos["nombre"] in curso.grupos():
            errores.append(f"El grupo {datos['nombre']} ya existe.")
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            modelo_grupo.crear(datos["nombre"], int(datos["grado"]))
            flash(f"Grupo {datos['nombre']} creado.", "exito")
            return redirect(url_for("cursos.lista", grupo=datos["nombre"]))
    return render_template("cursos/grupo_form.html", datos=datos, letras=LETRAS)


@cursos_bp.route("/grupos/eliminar", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def eliminar_grupo():
    nombre = request.form.get("nombre", "")
    if curso.listar(grupo=nombre) or curso.estudiantes_del_grupo(nombre):
        flash("Solo se puede eliminar un grupo vacío (sin asignaturas ni estudiantes).", "error")
        return redirect(url_for("cursos.lista", grupo=nombre))
    modelo_grupo.eliminar(nombre)
    flash(f"Grupo {nombre} eliminado.", "exito")
    return redirect(url_for("cursos.lista"))
