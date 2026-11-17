from datetime import datetime

from flask import Flask, render_template, session

from config import Config
import pymysql

from models.conexion import cerrar_bd, probar_conexion

from controllers.auth import auth_bp
from controllers.principal import principal_bp
from controllers.usuarios import usuarios_bp
from controllers.cursos import cursos_bp
from controllers.calificaciones import calificaciones_bp
from controllers.asistencia import asistencia_bp
from controllers.alertas import alertas_bp
from controllers.reportes import reportes_bp
from controllers.anuncios import anuncios_bp


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(principal_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(cursos_bp)
    app.register_blueprint(calificaciones_bp)
    app.register_blueprint(asistencia_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(anuncios_bp)

    app.teardown_appcontext(cerrar_bd)

    probar_conexion(app)

    @app.context_processor
    def datos_globales():
        return {
            "usuario_actual": {
                "id": session.get("usuario_id"),
                "nombre": session.get("nombre"),
                "rol": session.get("rol"),
            }
        }

    @app.template_filter("fecha_larga")
    def fecha_larga(valor):
        if not valor:
            return ""
        if isinstance(valor, str):
            valor = datetime.fromisoformat(valor)
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{valor.day} de {meses[valor.month - 1]} de {valor.year}"

    @app.errorhandler(403)
    def prohibido(e):
        return render_template("errores/error.html", codigo=403,
                               mensaje="No tienes permiso para ver esta página."), 403

    @app.errorhandler(404)
    def no_encontrado(e):
        return render_template("errores/error.html", codigo=404,
                               mensaje="La página que buscas no existe."), 404

    @app.errorhandler(pymysql.err.OperationalError)
    def error_mysql(e):
        return render_template("errores/error.html", codigo=503,
                               mensaje="No hay conexión con MySQL. Enciende MySQL en XAMPP e importa la base de datos."), 503

    @app.errorhandler(500)
    def error_servidor(e):
        return render_template("errores/error.html", codigo=500,
                               mensaje="Ocurrió un error interno. Intenta de nuevo."), 500

    return app


app = crear_app()

if __name__ == "__main__":
    app.run(debug=True)
