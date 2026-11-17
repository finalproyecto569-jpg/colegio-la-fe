from decimal import Decimal

import pymysql
import pymysql.cursors
from flask import g, current_app


def obtener_bd():
    if "bd" not in g:
        g.bd = pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.bd


def cerrar_bd(error=None):
    bd = g.pop("bd", None)
    if bd is not None:
        bd.close()


def _limpiar(fila):
    return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in fila.items()}


def consultar(sql, parametros=(), uno=False):
    with obtener_bd().cursor() as cursor:
        cursor.execute(sql, parametros)
        filas = [_limpiar(f) for f in cursor.fetchall()]
    if uno:
        return filas[0] if filas else None
    return filas


def ejecutar(sql, parametros=()):
    bd = obtener_bd()
    with bd.cursor() as cursor:
        cursor.execute(sql, parametros)
        nuevo_id = cursor.lastrowid
    bd.commit()
    return nuevo_id


def probar_conexion(app):
    try:
        conexion = pymysql.connect(host=app.config["DB_HOST"], port=app.config["DB_PORT"],
                                   user=app.config["DB_USER"], password=app.config["DB_PASSWORD"],
                                   database=app.config["DB_NAME"])
        conexion.close()
        print(f">> Conectado a MySQL: base de datos '{app.config['DB_NAME']}'")
    except pymysql.err.OperationalError as error:
        print("\n" + "!" * 60)
        print(" No se pudo conectar a MySQL:", error)
        print(" 1. Abre XAMPP y enciende MySQL (botón Start).")
        print(" 2. Importa database/seguimiento_academico.sql en phpMyAdmin.")
        print(" 3. Revisa usuario y contraseña en el archivo .env")
        print("!" * 60 + "\n")
