from flask import current_app
from models.conexion import consultar, ejecutar


def calcular_promedio(notas):
    pesos = current_app.config["PESOS_CORTES"]
    suma = 0
    suma_pesos = 0
    for corte, nota in notas.items():
        if nota is not None:
            suma += nota * pesos[corte]
            suma_pesos += pesos[corte]
    if suma_pesos == 0:
        return None
    return round(suma / suma_pesos, 2)


def notas_del_curso(id_curso):
    filas = consultar(
        """SELECT n.matricula_id, n.corte, n.nota
           FROM calificaciones n JOIN matriculas m ON m.id = n.matricula_id
           WHERE m.curso_id = %s""",
        (id_curso,))
    resultado = {}
    for f in filas:
        resultado.setdefault(f["matricula_id"], {1: None, 2: None, 3: None})
        resultado[f["matricula_id"]][f["corte"]] = f["nota"]
    return resultado


def guardar(id_matricula, corte, nota):
    ejecutar(
        """INSERT INTO calificaciones (matricula_id, corte, nota) VALUES (%s,%s,%s)
           ON DUPLICATE KEY UPDATE nota = VALUES(nota), fecha = NOW()""",
        (id_matricula, corte, nota))


def eliminar(id_matricula, corte):
    ejecutar("DELETE FROM calificaciones WHERE matricula_id = %s AND corte = %s", (id_matricula, corte))
