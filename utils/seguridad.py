from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_requerido(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para continuar.", "aviso")
            return redirect(url_for("auth.login"))
        return funcion(*args, **kwargs)
    return envoltura


def roles_permitidos(*roles):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Debes iniciar sesión para continuar.", "aviso")
                return redirect(url_for("auth.login"))
            if session.get("rol") not in roles:
                abort(403)
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


def puede_gestionar_curso(curso):
    if curso is None:
        return False
    rol = session.get("rol")
    if rol in ("administrador", "coordinador"):
        return True
    return rol == "docente" and curso["docente_id"] == session.get("usuario_id")


def docente_filtro():
    return session.get("usuario_id") if session.get("rol") == "docente" else None
