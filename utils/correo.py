import smtplib
from email.message import EmailMessage
from config import Config


def enviar_correo(destino, asunto, texto):
    if not Config.MAIL_USUARIO or not Config.MAIL_PASSWORD:
        print("Correo no configurado en el .env, no se envió el mensaje.")
        return False

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = Config.MAIL_USUARIO
    mensaje["To"] = destino
    mensaje.set_content(texto)

    try:
        if Config.MAIL_PUERTO == 465:
            servidor = smtplib.SMTP_SSL(Config.MAIL_SERVIDOR, 465, timeout=20)
        else:
            servidor = smtplib.SMTP(Config.MAIL_SERVIDOR, Config.MAIL_PUERTO, timeout=20)
            servidor.starttls()
        servidor.login(Config.MAIL_USUARIO, Config.MAIL_PASSWORD)
        servidor.send_message(mensaje)
        servidor.quit()
        return True
    except Exception as error:
        print("No se pudo enviar el correo a", destino, ":", error)
        return False


def avisar_inasistencia(estudiante, curso, fecha):
    asunto = "Aviso de inasistencia - Institución Educativa La Fe"
    texto = (
        f"Hola {estudiante['nombre']},\n\n"
        f"Te informamos que se registró una inasistencia en la asignatura "
        f"{curso['nombre']} el día {fecha}.\n\n"
        f"Si tienes una excusa, preséntala a tu docente o a coordinación.\n\n"
        f"Institución Educativa La Fe"
    )
    return enviar_correo(estudiante["correo"], asunto, texto)