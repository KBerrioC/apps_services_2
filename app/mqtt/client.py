import json
import logging
import os
from decimal import Decimal

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sm
from app.database.connection import SessionLocal
from app.schemas.medicion import MensajeMQTT

load_dotenv()

logger = logging.getLogger("mqtt")

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "")
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

# El tópico es iot/sensors/{sensor_id}/data, el sensor asignado es la tercera parte
SENSOR_ASIGNADO = TOPIC.split("/")[2] if TOPIC.count("/") >= 3 else ""


def _resumen_errores(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()
    )


def procesar_mensaje(db: Session, raw: bytes, sensor_asignado: str) -> tuple[bool, str]:
    """Valida y guarda un mensaje. Devuelve (aceptado, motivo)."""
    # 1. JSON
    try:
        datos = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return False, f"JSON inválido: {error}"

    # 2. Estructura, tipos y timestamp (Pydantic)
    try:
        mensaje = MensajeMQTT.model_validate(datos)
    except ValidationError as error:
        return False, f"estructura inválida: {_resumen_errores(error)}"

    # 3. Sensor: existe, es el asignado y está activo (ORM)
    sensor = crud_sensor.get_sensor_por_codigo(db, mensaje.sensor_id)
    if sensor is None:
        return False, f"sensor inexistente: {mensaje.sensor_id}"
    if sensor.codigo != sensor_asignado:
        return False, f"el sensor {sensor.codigo} no es el asignado ({sensor_asignado})"
    if not sensor.activo:
        return False, f"el sensor {sensor.codigo} está inactivo"

    # 4. Magnitud, unidad y rango de cada medición
    catalogo = {m.magnitud: m for m in crud_sm.get_magnitudes_por_sensor(db, sensor.id)}
    registros: list[tuple[int, Decimal]] = []
    for nombre, dato in mensaje.measurements.items():
        sm = catalogo.get(nombre)
        if sm is None:
            return False, f"magnitud '{nombre}' no existe para el sensor {sensor.codigo}"
        if dato.unit != sm.unidad:
            return False, (
                f"unidad incorrecta en '{nombre}': recibida '{dato.unit}', "
                f"esperada '{sm.unidad}'"
            )
        valor = Decimal(str(dato.value))
        if not (sm.valor_minimo <= valor <= sm.valor_maximo):
            return False, (
                f"valor fuera de rango en '{nombre}': {valor} "
                f"(permitido {sm.valor_minimo} a {sm.valor_maximo})"
            )
        registros.append((sm.id, valor))

    # 5. Todo válido: se guardan todas las magnitudes con el mismo timestamp
    crud_medicion.create_mediciones(db, registros, mensaje.timestamp)
    return True, f"{len(registros)} mediciones guardadas ({mensaje.timestamp.isoformat()})"


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code.is_failure:
        logger.error("Error de conexión MQTT: %s", reason_code)
        return
    logger.info("Conectado al broker %s:%s", BROKER, PORT)
    client.subscribe(TOPIC)
    logger.info("Suscrito al tópico %s", TOPIC)


def on_message(client, userdata, message):
    texto = message.payload.decode("utf-8", errors="replace")
    db = SessionLocal()
    try:
        aceptado, motivo = procesar_mensaje(db, message.payload, SENSOR_ASIGNADO)
    except Exception:
        db.rollback()
        logger.exception("Error inesperado procesando: %s", texto)
        return
    finally:
        db.close()

    if aceptado:
        logger.info("ACEPTADO: %s", motivo)
    else:
        logger.warning("RECHAZADO: %s | mensaje: %s", motivo, texto)


def create_client() -> mqtt.Client:
    if not BROKER or not SENSOR_ASIGNADO:
        raise RuntimeError("Revisa MQTT_BROKER y MQTT_TOPIC en el archivo .env")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USERNAME:
        client.username_pw_set(USERNAME, PASSWORD or "")
    client.on_connect = on_connect
    client.on_message = on_message
    return client