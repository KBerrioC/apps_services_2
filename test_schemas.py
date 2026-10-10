from pydantic import ValidationError

from app.schemas.medicion import MensajeMQTT


def mensaje(**cambios):
    base = {
        "sensor_id": "AQ-005",
        "timestamp": "2026-10-10T00:01:05Z",
        "measurements": {"pm10": {"value": 74.71, "unit": "ug/m3"}},
    }
    base.update(cambios)
    return base


casos = {
    "válido": mensaje(),
    "valor como texto": mensaje(measurements={"pm10": {"value": "abc", "unit": "ug/m3"}}),
    "timestamp inválido": mensaje(timestamp="ayer"),
    "timestamp sin zona": mensaje(timestamp="2026-10-10T00:01:05"),
    "sin measurements": mensaje(measurements={}),
}

for nombre, datos in casos.items():
    try:
        m = MensajeMQTT.model_validate(datos)
        print(f"{nombre}: OK -> {m.timestamp}")
    except ValidationError as e:
        print(f"{nombre}: RECHAZADO ({e.errors()[0]['msg']})")