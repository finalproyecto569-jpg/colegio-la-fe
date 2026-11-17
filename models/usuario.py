from werkzeug.security import generate_password_hash
from models.conexion import consultar, ejecutar

ROLES = ["administrador", "coordinador", "docente", "estudiante"]


def listar(texto="", rol=""):
    sql = "SELECT * FROM usuarios WHERE 1=1"
    parametros = []
    if texto:
        sql += " AND (nombre LIKE %s OR correo LIKE %s OR documento LIKE %s)"
        parametros += [f"%{texto}%"] * 3
    if rol:
        sql += " AND rol = %s"
        parametros.append(rol)
    sql += " ORDER BY rol, nombre"
    return consultar(sql, parametros)


def obtener(id_usuario):
    return consultar("SELECT * FROM usuarios WHERE id = %s", (id_usuario,), uno=True)


def obtener_por_correo(correo):
    return consultar("SELECT * FROM usuarios WHERE correo = %s", (correo,), uno=True)


def existe_dato(campo, valor, excepto_id=None):
    sql = f"SELECT id FROM usuarios WHERE {campo} = %s"
    parametros = [valor]
    if excepto_id:
        sql += " AND id <> %s"
        parametros.append(excepto_id)
    return consultar(sql, parametros, uno=True) is not None


def crear(datos):
    return ejecutar(
        "INSERT INTO usuarios (nombre, documento, correo, password, rol, programa, activo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (datos["nombre"], datos["documento"], datos["correo"],
         generate_password_hash(datos["password"]), datos["rol"], datos["programa"] or None, datos["activo"]),
    )


def actualizar(id_usuario, datos):
    ejecutar(
        "UPDATE usuarios SET nombre=%s, documento=%s, correo=%s, rol=%s, programa=%s, activo=%s WHERE id=%s",
        (datos["nombre"], datos["documento"], datos["correo"], datos["rol"],
         datos["programa"] or None, datos["activo"], id_usuario),
    )
    if datos.get("password"):
        ejecutar("UPDATE usuarios SET password=%s WHERE id=%s",
                 (generate_password_hash(datos["password"]), id_usuario))


def eliminar(id_usuario):
    ejecutar("DELETE FROM usuarios WHERE id = %s", (id_usuario,))


def listar_por_rol(rol):
    return consultar("SELECT * FROM usuarios WHERE rol = %s AND activo = 1 ORDER BY nombre", (rol,))


def contar_por_rol():
    filas = consultar("SELECT rol, COUNT(*) AS total FROM usuarios GROUP BY rol")
    return {f["rol"]: f["total"] for f in filas}


def programas():
    filas = consultar("SELECT DISTINCT programa FROM usuarios WHERE programa IS NOT NULL ORDER BY programa")
    return [f["programa"] for f in filas]
