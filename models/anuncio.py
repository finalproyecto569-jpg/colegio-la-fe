from models.conexion import consultar, ejecutar


def listar(limite=None):
    sql = """SELECT a.*, u.nombre AS autor FROM anuncios a
             LEFT JOIN usuarios u ON u.id = a.autor_id
             ORDER BY a.fecha_publicacion DESC, a.id DESC"""
    if limite:
        sql += " LIMIT %s"
        return consultar(sql, (limite,))
    return consultar(sql)


def obtener(id_anuncio):
    return consultar("SELECT * FROM anuncios WHERE id = %s", (id_anuncio,), uno=True)


def crear(datos, autor_id):
    return ejecutar(
        "INSERT INTO anuncios (titulo, descripcion, fecha_evento, imagen, autor_id) VALUES (%s,%s,%s,%s,%s)",
        (datos["titulo"], datos["descripcion"], datos["fecha_evento"] or None, datos["imagen"] or None, autor_id))


def actualizar(id_anuncio, datos):
    ejecutar(
        "UPDATE anuncios SET titulo=%s, descripcion=%s, fecha_evento=%s, imagen=%s WHERE id=%s",
        (datos["titulo"], datos["descripcion"], datos["fecha_evento"] or None, datos["imagen"] or None, id_anuncio))


def eliminar(id_anuncio):
    ejecutar("DELETE FROM anuncios WHERE id = %s", (id_anuncio,))
