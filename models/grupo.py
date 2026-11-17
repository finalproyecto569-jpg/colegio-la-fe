from models.conexion import consultar, ejecutar


def listar():
    return consultar("SELECT * FROM grupos ORDER BY grado, nombre")


def obtener(nombre):
    return consultar("SELECT * FROM grupos WHERE nombre = %s", (nombre,), uno=True)


def grado_de(nombre):
    digitos = "".join(ch for ch in nombre if ch.isdigit())
    return int(digitos) if digitos else None


def crear(nombre, grado):
    ejecutar("INSERT INTO grupos (nombre, grado) VALUES (%s, %s)", (nombre, grado))


def asegurar(nombre, grado=None):
    if nombre and obtener(nombre) is None:
        crear(nombre, grado or grado_de(nombre) or 1)


def eliminar(nombre):
    ejecutar("DELETE FROM grupos WHERE nombre = %s", (nombre,))
