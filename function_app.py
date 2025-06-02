import azure.functions as func
import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.twiml.voice_response import VoiceResponse

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="SendAlert", methods=["POST"])
def send_alert(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a SendAlert request.')

    try:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        twilio_phone = os.environ["TWILIO_PHONE_NUMBER"]
        # Obtener el número del usuario desde una variable de entorno
        user_phone = os.environ.get("USER_PHONE_TO_ALERT", "+529992753968") # Valor por defecto si no se establece
    except KeyError as e:
        logging.error(f"Error: Variable de entorno no configurada: {e}")
        return func.HttpResponse(
             f"Error de configuración: La variable de entorno {e} no está definida. Por favor, configúrela en local.settings.json.",
             status_code=500
        )

    logging.info(f"SID de cuenta Twilio: {account_sid[:5]}...") # No loguear el token completo
    logging.info(f"Número de Twilio: {twilio_phone}")
    logging.info(f"Número de usuario para alertar: {user_phone}")

    client = Client(account_sid, auth_token)

    # Simular evento de respaldo (en un caso real, esto vendría del request o de otro servicio)
    backup_data = {
        "status": "EXITO",
        "db_name": "MySQL_Inventario",
        "timestamp": "2024-05-20 22:00:00",
        "size": "2.5GB"
    }
    # Mensaje para SMS (y anteriormente WhatsApp)
    # Simplificado para SMS y corregido el uso de saltos de línea
    alert_message_text = (
        f"Respaldo de BD Completo\n"
        f"Base de datos: {backup_data['db_name']}\n"
        f"Estado: {backup_data['status']}\n"
        f"Tamaño: {backup_data['size']}\n"
        f"Hora: {backup_data['timestamp']}"
    )

    # Mensaje para llamada de voz
    alert_message_voice = (
        f"Alerta de sistema: Respaldo de {backup_data['db_name']} completado exitosamente. "
        f"Tamaño: {backup_data['size']}. Hora del respaldo: {backup_data['timestamp']}"
    )

    sms_sid = None
    call_sid = None
    errors = []

    # Enviar SMS
    try:
        logging.info(f"Intentando enviar SMS a: {user_phone} desde: {twilio_phone}")
        sms_message = client.messages.create(
            body=alert_message_text,
            from_=twilio_phone, # Usar el número de Twilio directamente para SMS
            to=user_phone      # Usar el número del usuario directamente para SMS
        )
        sms_sid = sms_message.sid
        logging.info(f"SMS enviado exitosamente. SID: {sms_sid}")
    except TwilioRestException as e:
        logging.error(f"Error al enviar SMS: {e}")
        errors.append(f"Error SMS: {e.status} - {e.msg}")
    except Exception as e:
        logging.error(f"Error inesperado al enviar SMS: {e}")
        errors.append(f"Error inesperado SMS: {str(e)}")


    # Crear llamada de voz
    try:
        logging.info(f"Intentando realizar llamada a: {user_phone} desde: {twilio_phone}")
        response_twiml = VoiceResponse()
        response_twiml.say(
            alert_message_voice,
            voice="woman",
            language="es-MX"
        )
        call = client.calls.create(
            twiml=str(response_twiml),
            to=user_phone,
            from_=twilio_phone
        )
        call_sid = call.sid
        logging.info(f"Llamada creada exitosamente. SID: {call_sid}")
    except TwilioRestException as e:
        logging.error(f"Error al crear la llamada: {e}")
        errors.append(f"Error Llamada: {e.status} - {e.msg}")
    except Exception as e:
        logging.error(f"Error inesperado al crear la llamada: {e}")
        errors.append(f"Error inesperado Llamada: {str(e)}")

    # Construir la respuesta
    response_messages = []
    if sms_sid:
        response_messages.append(f"SMS SID: {sms_sid}")
    if call_sid:
        response_messages.append(f"Llamada SID: {call_sid}")

    if not errors and (sms_sid or call_sid) :
        return func.HttpResponse(
            f"✅ Alertas procesadas:\n" + "\n".join(response_messages),
            status_code=200
        )
    elif errors:
        error_summary = "\n".join(errors)
        details = "\n".join(response_messages)
        return func.HttpResponse(
            f"⚠️ Alertas procesadas con errores:\n{details}\nErrores:\n{error_summary}\nRevise los logs de la función y el panel de Twilio para más detalles.",
            status_code=500 # O 207 Multi-Status si algunas partes tuvieron éxito
        )
    else:
        return func.HttpResponse(
            "🤷 No se pudo enviar ninguna alerta y no se capturaron errores específicos de Twilio. Verifique la configuración y los logs.",
            status_code=500
        )
