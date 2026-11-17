import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-de-desarrollo-cambiar")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "seguimiento_academico")
    DB_SSL = os.getenv("DB_SSL", "false").lower() == "true"

    MAIL_SERVIDOR = os.getenv("MAIL_SERVIDOR", "smtp.gmail.com")
    MAIL_PUERTO = int(os.getenv("MAIL_PUERTO", "587"))
    MAIL_USUARIO = os.getenv("MAIL_USUARIO", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

    NOTA_MINIMA = float(os.getenv("NOTA_MINIMA", "3.0"))
    MAX_INASISTENCIA = float(os.getenv("MAX_INASISTENCIA", "20"))

    PESOS_CORTES = {1: 0.30, 2: 0.30, 3: 0.40}
