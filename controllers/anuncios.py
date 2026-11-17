import os
import time
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session, current_app
from werkzeug.utils import secure_filename
from models import anuncio
from utils.seguridad import roles_permitidos

anuncios_bp = Blueprint("anuncios", __name__, url_prefix="/anuncios")

EXTENSIONES = {"jpg", "jpeg", "png", "webp", "gif"}


def guardar_imagen(archivo):
    if not archivo or archivo.filename == "":
        return None
    extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if extension not in EXTENSIONES:
        return "error"
    nombre = f"{int(time.time())}_{secure_filename(archivo.filename)}"
    carpeta = os.path.join(current_app.static_folder, "uploads", "anuncios")
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre))
    return f"uploads/anuncios/{nombre}"


def leer_formulario():
    return {
        "titulo": request.form.get("titulo", "").strip(),
        "descripcion": request.form.get("descripcion", "").strip(),
        "fecha_evento": request.form.get("fecha_evento", "").strip(),
    }


def validar(datos):
    errores = []
    if len(datos["titulo"]) < 5:
        errores.append("El título debe tener al menos 5 caracteres.")
    if len(datos["descripcion"]) < 10:
        errores.append("La descripción debe tener al menos 10 caracteres.")
    if datos["fecha_evento"]:
        try:
            datetime.strptime(datos["fecha_evento"], "%Y-%m-%d")
        except ValueError:
            errores.append("La fecha del evento no es válida.")
    return errores


@anuncios_bp.route("/nuevo", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador")
def nuevo():
    datos = {}
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos)
        imagen = guardar_imagen(request.files.get("imagen"))
        if imagen == "error":
            errores.append("La imagen debe ser JPG, PNG, WEBP o GIF.")
        if errores:
            for e in errores:
                flash(e, "error")
        else:
            datos["imagen"] = imagen
            anuncio.crear(datos, session["usuario_id"])
            flash("Anuncio publicado.", "exito")
            return redirect(url_for("principal.inicio"))
    return render_template("anuncios/form.html", datos=datos, editando=False)


@anuncios_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@roles_permitidos("administrador", "coordinador")
def editar(id):
    a = anuncio.obtener(id)
    if a is None:
        abort(404)
    datos = dict(a)
    if request.method == "POST":
        datos = leer_formulario()
        errores = validar(datos)
        imagen = guardar_imagen(request.files.get("imagen"))
        if imagen == "error":
            errores.append("La imagen debe ser JPG, PNG, WEBP o GIF.")
        if errores:
            for e in errores:
                flash(e, "error")
            datos["imagen"] = a["imagen"]
        else:
            if imagen:
                datos["imagen"] = imagen
            elif request.form.get("quitar_imagen"):
                datos["imagen"] = None
            else:
                datos["imagen"] = a["imagen"]
            anuncio.actualizar(id, datos)
            flash("Anuncio actualizado.", "exito")
            return redirect(url_for("principal.inicio"))
    datos["id"] = id
    return render_template("anuncios/form.html", datos=datos, editando=True)


@anuncios_bp.route("/<int:id>/eliminar", methods=["POST"])
@roles_permitidos("administrador", "coordinador")
def eliminar(id):
    if anuncio.obtener(id) is None:
        flash("El anuncio no existe.", "error")
    else:
        anuncio.eliminar(id)
        flash("Anuncio eliminado.", "exito")
    return redirect(url_for("principal.inicio"))
