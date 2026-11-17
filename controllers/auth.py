from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("principal.inicio"))

    correo = ""
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        clave = request.form.get("password", "")

        if not correo or not clave:
            flash("Escribe tu correo y tu contraseña.", "error")
        else:
            u = usuario.obtener_por_correo(correo)
            if u is None or not check_password_hash(u["password"], clave):
                flash("Correo o contraseña incorrectos.", "error")
            elif not u["activo"]:
                flash("Tu cuenta está desactivada. Contacta al administrador.", "error")
            else:
                session.clear()
                session["usuario_id"] = u["id"]
                session["nombre"] = u["nombre"]
                session["rol"] = u["rol"]
                flash(f"¡Bienvenido(a), {u['nombre']}!", "exito")
                return redirect(url_for("principal.inicio"))

    return render_template("auth/login.html", correo=correo)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "exito")
    return redirect(url_for("auth.login"))
