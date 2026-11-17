import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from models import usuario, curso
from models import grupo as modelo_grupo
from utils.seguridad import roles_permitidos

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def leer_formulario():
    return {
        "nombre": request.form.get("nombre", "").strip(),
        "documento": request.form.get("documento", "").strip(),
        "correo": request.form.get("correo", "").strip().lower(),
        "password": request.form.get("password", ""),
        "rol": request.form.get("rol", ""),
        "programa": request.form.get("programa", "").strip().upper(),
        "activo": 1 if request.form.get("activo") else 0,
    }


def validar(datos, id_usuario=None):
    errores = []
    if len(datos["nombre"]) < 3:
        errores.append("El nombre debe tener al menos 3 letras.")
    if not datos["documento"].isdigit() or not 6 <= len(datos["documento"]) <= 12:
        errores.append("El documento debe tener entre 6 y 12 números.")
    if not PATRON_CORREO.match(datos["correo"]):
        errores.append("El correo no es válido.")
    if datos["rol"] not in usuario.ROLES:
        errores.append("Selecciona un rol válido.")
    if datos["rol"] == "estudiante" and not datos["programa"]:
        errores.append("El estudiante debe tener grado y grupo (ej: 9°A).")
    if id_usuario is None or datos["password"]:
        if len(datos["password"]) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
    if usuario.existe_dato("correo", datos["correo"], id_usuario):
        errores.append("Ya existe un usuario con ese correo.")
    if usuario.existe_dato("documento", datos["documento"], id_usuario):
        errores.append("Ya existe un usuario con ese documento.")
    return errores


def matricular_automaticamente(id_estudiante, datos):
    if datos["rol"] == "estudiante" and datos["programa"]:
        modelo_grupo.asegurar(datos["programa"])
        n = curso.matricular_en_grupo(id_estudiante, datos["programa"])
        if n:
            flash(f"Se matriculó automáticamente en {n} asignatura(s) del grupo {datos['programa']}.", "exito")
        elif datos["programa"] not in curso.grupos_con_asignaturas():
            flash(f"El grupo {datos['programa']} todavía no tiene asignaturas. Cuando crees una "
                  "asignatura con ese grupo, el estudiante se matriculará automáticamente.", "aviso")


@usuarios_bp.route("/")
@roles_permitidos("administrador")
def lista():
    texto = request.args.get("q", "").strip()
    rol = request.args.get("rol", "")
    return render_template("usuarios/lista.html", usuarios=usuario.listar(texto, rol),
                           roles=usuario.ROLES, texto=texto, rol=rol, conteo=usuario.contar_por_rol())


@usuarios_bp.route("/api")
@roles_permitidos("administrador", "coordinador", "docente")
def api_buscar():
    texto = request.args.get("q", "").strip()
    rol = request.args.get("rol", "")
    datos = [
        {"id": u["id"], "nombre": u["nombre"], "documento": u["documento"], "correo": u["correo"],
         "rol": u["rol"], "programa": u["programa"] or "", "activo": bool(u["activo"])}
        for u in usuario.listar(texto, rol)
    ]
    return jsonify(datos)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@roles_permitidos("administrador")
def nuevo():
    datos = {"activo": 1}
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos)
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            nuevo_id = usuario.crear(datos)
            flash("Usuario registrado correctamente.", "exito")
            matricular_automaticamente(nuevo_id, datos)
            return redirect(url_for("usuarios.lista"))
    return render_template("usuarios/form.html", datos=datos, roles=usuario.ROLES,
                           programas=sorted(set(usuario.programas()) | set(curso.grupos())), editando=False)


@usuarios_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@roles_permitidos("administrador")
def editar(id):
    u = usuario.obtener(id)
    if u is None:
        abort(404)
    datos = dict(u)
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos, id)
        if id == session["usuario_id"] and (datos["rol"] != "administrador" or not datos["activo"]):
            errores.append("No puedes quitarte el rol de administrador ni desactivar tu propia cuenta.")
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            usuario.actualizar(id, datos)
            flash("Usuario actualizado correctamente.", "exito")
            matricular_automaticamente(id, datos)
            return redirect(url_for("usuarios.lista"))
    datos["id"] = id
    return render_template("usuarios/form.html", datos=datos, roles=usuario.ROLES,
                           programas=sorted(set(usuario.programas()) | set(curso.grupos())), editando=True)


@usuarios_bp.route("/<int:id>/eliminar", methods=["POST"])
@roles_permitidos("administrador")
def eliminar(id):
    if id == session["usuario_id"]:
        flash("No puedes eliminar tu propia cuenta.", "error")
    elif usuario.obtener(id) is None:
        flash("El usuario no existe.", "error")
    else:
        usuario.eliminar(id)
        flash("Usuario eliminado.", "exito")
    return redirect(url_for("usuarios.lista"))
