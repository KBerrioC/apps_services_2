from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.database.connection import SessionLocal
from app.mqtt.client import SENSOR_ASIGNADO, procesar_mensaje
import json

db = SessionLocal()
sensor = crud_sensor.get_sensor_por_codigo(db, SENSOR_ASIGNADO)
otro = next(s for s in crud_sensor.get_sensores(db) if s.codigo != SENSOR_ASIGNADO)


def msg(sensor_id=SENSOR_ASIGNADO, ts="2026-10-10T00:01:05Z", medidas=None):
    medidas = medidas or {"pm10": {"value": 74.71, "unit": "ug/m3"}}
    return json.dumps(
        {"sensor_id": sensor_id, "timestamp": ts, "measurements": medidas}
    ).encode()


casos = {
    "JSON roto": b"{esto no es json",
    "sensor inexistente": msg(sensor_id="ZZ-999"),
    "sensor de otro grupo": msg(sensor_id=otro.codigo),
    "unidad incorrecta": msg(medidas={"pm10": {"value": 74.7, "unit": "mg/m3"}}),
    "tipo de dato incorrecto": msg(medidas={"pm10": {"value": "abc", "unit": "ug/m3"}}),
    "magnitud incorrecta": msg(medidas={"temperature": {"value": 24.6, "unit": "C"}}),
    "timestamp inválido": msg(ts="ayer"),
    "valor fuera de rango": msg(medidas={"pm1_0": {"value": 500.0, "unit": "ug/m3"}}),
    "una magnitud válida y otra con unidad mala": msg(
        medidas={
            "pm10": {"value": 74.7, "unit": "ug/m3"},
            "pm2_5": {"value": 14.6, "unit": "mg/m3"},
        }
    ),
}

antes = len(crud_medicion.get_mediciones(db, sensor.id))
for nombre, raw in casos.items():
    aceptado, motivo = procesar_mensaje(db, raw, SENSOR_ASIGNADO)
    estado = "ACEPTADO (ERROR!)" if aceptado else "RECHAZADO"
    print(f"{nombre}: {estado} -> {motivo}")
despues = len(crud_medicion.get_mediciones(db, sensor.id))
print(f"\nMediciones antes: {antes}, después: {despues}")
print("OK: no se guardó ningún dato inválido" if antes == despues else "REVISAR: se guardó algo")
db.close()