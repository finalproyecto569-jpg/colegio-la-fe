from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import alerta, curso, usuario
from models.conexion import consultar
from utils.seguridad import roles_permitidos, docente_filtro

alertas_bp = Blueprint("alertas", __name__, url_prefix="/alertas")


def opciones_formulario():
    id_docente = docente_filtro()
    if id_docente:
        estudiantes = consultar(
            """SELECT DISTINCT u.id, u.nombre, u.documento FROM usuarios u
               JOIN matriculas m ON m.estudiante_id = u.id
               JOIN cursos c ON c.id = m.curso_id
               WHERE c.docente_id = %s ORDER BY u.nombre""", (id_docente,))
    else:
        estudiantes = usuario.listar_por_rol("estudiante")
    return estudiantes, curso.listar(docente_id=id_docente)


def leer_formulario():
    return {
        "estudiante_id": request.form.get("estudiante_id", ""),
        "curso_id": request.form.get("curso_id", ""),
        "tipo": request.form.get("tipo", ""),
        "nivel": request.form.get("nivel", ""),
        "estado": request.form.get("estado", "abierta"),
        "descripcion": request.form.get("descripcion", "").strip(),
        "seguimiento": request.form.get("seguimiento", "").strip(),
    }


def validar(datos, estudiantes, cursos):
    errores = []
    if not datos["estudiante_id"].isdigit() or int(datos["estudiante_id"]) not in [e["id"] for e in estudiantes]:
        errores.append("Selecciona un estudiante válido.")
    if datos["curso_id"] and (not datos["curso_id"].isdigit()
                              or int(datos["curso_id"]) not in [c["id"] for c in cursos]):
        errores.append("Selecciona un curso válido.")
    if datos["tipo"] not in alerta.TIPOS:
        errores.append("Selecciona el tipo de alerta.")
    if datos["nivel"] not in alerta.NIVELES:
        errores.append("Selecciona el nivel de la alerta.")
    if datos["estado"] not in alerta.ESTADOS:
        errores.append("Selecciona un estado válido.")
    if len(datos["descripcion"]) < 10:
        errores.append("La descripción debe tener al menos 10 caracteres.")
    if datos["estado"] == "cerrada" and not datos["seguimiento"]:
        errores.append("Para cerrar la alerta escribe las acciones de seguimiento realizadas.")
    return errores


def alerta_permitida(id_alerta):
    a = alerta.obtener(id_alerta)
    if a is None:
        abort(404)
    if session["rol"] == "docente" and a["docente_id"] != session["usuario_id"] \
            and a["creado_por"] != session["usuario_id"]:
        abort(403)
    return a


def grupos_visibles():
    return [g["grupo"] for g in curso.resumen_grupos(docente_filtro()) if g["grupo"] != "SIN GRUPO"]


@alertas_bp.route("/")
@roles_permitidos("administrador", "coordinador", "docente")
def lista():
    if not request.args:
        tarjetas = []
        for g in grupos_visibles():
            conteo = alerta.contar_por("estado", docente_id=docente_filtro(), grupo=g)
            tarjetas.append({"grupo": g, "abiertas": conteo.get("abierta", 0),
                             "seguimiento": conteo.get("en_seguimiento", 0),
                             "cerradas": conteo.get("cerrada", 0)})
        return render_template("alertas/grupos.html", tarjetas=tarjetas)

    filtros = {
        "estado": request.args.get("estado", ""),
        "nivel": request.args.get("nivel", ""),
        "tipo": request.args.get("tipo", ""),
        "texto": request.args.get("q", "").strip(),
        "grupo": request.args.get("grupo", ""),
    }
    alertas = alerta.listar(**filtros, docente_id=docente_filtro())
    return render_template("alertas/lista.html", alertas=alertas, filtros=filtros,
                           tipos=alerta.TIPOS, niveles=alerta.NIVELES, estados=alerta.ESTADOS,
                           grupos=grupos_visibles(),
                           conteo=alerta.contar_por("estado", docente_id=docente_filtro(), grupo=filtros["grupo"]))


def volver_a_lista(id_estudiante):
    est = usuario.obtener(id_estudiante) if str(id_estudiante).isdigit() else None
    if est and est["programa"]:
        return redirect(url_for("alertas.lista", grupo=est["programa"]))
    return redirect(url_for("alertas.lista", estado=""))


@alertas_bp.route("/nueva", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def nueva():
    estudiantes, cursos = opciones_formulario()
    datos = {"estado": "abierta", "nivel": "media",
             "estudiante_id": request.args.get("estudiante", ""), "curso_id": request.args.get("curso", "")}
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos, estudiantes, cursos)
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            alerta.crear(datos, creado_por=session["usuario_id"])
            flash("Alerta registrada.", "exito")
            return volver_a_lista(datos["estudiante_id"])
    return render_template("alertas/form.html", datos=datos, estudiantes=estudiantes, cursos=cursos,
                           tipos=alerta.TIPOS, niveles=alerta.NIVELES, estados=alerta.ESTADOS, editando=False)


@alertas_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def editar(id):
    a = alerta_permitida(id)
    estudiantes, cursos = opciones_formulario()
    datos = {k: (str(v) if v is not None else "") for k, v in dict(a).items()}
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos, estudiantes, cursos)
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            alerta.actualizar(id, datos)
            flash("Alerta actualizada.", "exito")
            return volver_a_lista(datos["estudiante_id"])
    datos["id"] = id
    datos["origen"] = a["origen"]
    datos["fecha_creacion"] = a["fecha_creacion"]
    return render_template("alertas/form.html", datos=datos, estudiantes=estudiantes, cursos=cursos,
                           tipos=alerta.TIPOS, niveles=alerta.NIVELES, estados=alerta.ESTADOS, editando=True)


@alertas_bp.route("/<int:id>/eliminar", methods=["POST"])
@roles_permitidos("administrador", "coordinador", "docente")
def eliminar(id):
    a = alerta_permitida(id)
    alerta.eliminar(id)
    flash("Alerta eliminada.", "exito")
    return volver_a_lista(a["estudiante_id"])


@alertas_bp.route("/generar", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def generar():
    nuevas = alerta.generar_automaticas(creado_por=session["usuario_id"])
    if nuevas:
        flash(f"Se generaron {nuevas} alerta(s) nueva(s).", "exito")
    else:
        flash("No hay alertas nuevas: todos los casos ya tienen seguimiento.", "aviso")
    return redirect(url_for("alertas.lista"))
